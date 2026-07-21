from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from .motion_format import load_motion
from .robot_asset import CONTROLLED_JOINT_NAMES


def _sample_motion(timestamps: np.ndarray, positions: np.ndarray, t: float) -> np.ndarray:
    if t <= timestamps[0]:
        return positions[0]
    if t >= timestamps[-1]:
        return positions[-1]
    idx = int(np.searchsorted(timestamps, t, side="right"))
    left = idx - 1
    right = idx
    span = max(float(timestamps[right] - timestamps[left]), 1.0e-9)
    alpha = (t - timestamps[left]) / span
    return (1.0 - alpha) * positions[left] + alpha * positions[right]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay MindBot joint motion in the official Isaac Lab environment.")
    parser.add_argument("--motion", required=True, type=Path)
    parser.add_argument("--task", default="Mindbot-DualArmWaist-Realsense-Play-v0")
    parser.add_argument("--num_envs", type=int, default=1)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--record-path", type=Path, default=None)
    parser.add_argument("--disable_fabric", action="store_true", default=False)
    parser.add_argument("--real-time", action="store_true", default=True)
    parser.add_argument("--no-real-time", action="store_false", dest="real_time")
    return parser.parse_args()


def main() -> None:
    args_cli = parse_args()

    from isaaclab.app import AppLauncher

    app_parser = argparse.ArgumentParser(add_help=False)
    AppLauncher.add_app_launcher_args(app_parser)
    app_args, _ = app_parser.parse_known_args()
    for key, value in vars(args_cli).items():
        setattr(app_args, key, value)
    if "Realsense" in args_cli.task and hasattr(app_args, "enable_cameras"):
        app_args.enable_cameras = True
    if args_cli.record and hasattr(app_args, "video"):
        app_args.video = True

    app_launcher = AppLauncher(app_args)
    simulation_app = app_launcher.app

    import gymnasium as gym  # noqa: PLC0415
    import torch  # noqa: PLC0415

    import mindbot_isaac_sim.tasks  # noqa: F401, PLC0415
    from isaaclab_tasks.utils import parse_env_cfg  # noqa: PLC0415
    from mindbot_isaac_sim.interfaces import make_joint_position_action  # noqa: PLC0415

    try:
        motion = load_motion(args_cli.motion)
        joint_names = motion["joint_names"]
        if tuple(joint_names) != CONTROLLED_JOINT_NAMES:
            missing = [name for name in joint_names if name not in CONTROLLED_JOINT_NAMES]
            if missing:
                raise RuntimeError(f"Motion contains unknown MindBot joints: {missing}")
        timestamps = motion["timestamps"]
        positions = motion["joint_positions"]
        if len(timestamps) != len(positions):
            raise RuntimeError("Motion timestamps and joint_positions length mismatch.")

        env_cfg = parse_env_cfg(
            args_cli.task,
            device=app_args.device,
            num_envs=args_cli.num_envs,
            use_fabric=not args_cli.disable_fabric,
        )
        env = gym.make(args_cli.task, cfg=env_cfg)
        env.reset()

        step_dt = float(getattr(env.unwrapped, "step_dt", 1.0 / max(motion["fps"], 1.0)))
        duration = float(timestamps[-1])
        playback_t = 0.0
        last_wall = time.time()
        paused = False
        print(f"[INFO] Replaying {args_cli.motion} with joints: {joint_names}", flush=True)

        with torch.inference_mode():
            while simulation_app.is_running():
                now = time.time()
                wall_dt = now - last_wall
                last_wall = now
                if not paused:
                    playback_t += wall_dt * max(args_cli.speed, 1.0e-6)
                if playback_t > duration:
                    if args_cli.loop:
                        playback_t = 0.0
                    else:
                        break
                target = _sample_motion(timestamps, positions, playback_t)
                action = make_joint_position_action(
                    env,
                    {name: float(value) for name, value in zip(joint_names, target)},
                    clamp_to_limits=True,
                )
                env.step(action)
                if args_cli.real_time and not getattr(app_args, "headless", False):
                    time.sleep(step_dt)

        env.close()
    finally:
        simulation_app.close()


if __name__ == "__main__":
    main()
