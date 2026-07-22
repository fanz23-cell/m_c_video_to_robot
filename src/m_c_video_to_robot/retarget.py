from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .filters import filter_joint_trajectory
from .gvhmr_loader import extract_yaw_from_human_frames
from .human_frame_transform import transform_human_frames_to_mindbot_workspace
from .limits import limits_arrays, validate_motion
from .motion_format import write_motion_bundle
from .paths import relative_to_repo, repo_path
from .robot_asset import CONTROLLED_JOINT_NAMES, ROBOT_NAME, assert_expected_controlled_joints, generated_model_path, load_official_spec


def _git_commit(path: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _load_filter_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _qpos_joint_value(model, qpos: np.ndarray, joint_name: str) -> float:
    import mujoco as mj

    joint_id = mj.mj_name2id(model, mj.mjtObj.mjOBJ_JOINT, joint_name)
    if joint_id < 0:
        raise KeyError(f"MuJoCo model is missing joint {joint_name!r}")
    qpos_adr = int(model.jnt_qposadr[joint_id])
    return float(qpos[qpos_adr])


def _ensure_model_exists(force: bool = False) -> Path:
    model_path = generated_model_path(prefer_xml=True)
    if model_path.exists() and not force and _model_has_required_bodies(model_path, ("left_arm_tcp", "right_arm_tcp")):
        return model_path
    from .build_model import build_model

    return build_model(force=True)


def _model_has_required_bodies(model_path: Path, body_names: tuple[str, ...]) -> bool:
    try:
        import mujoco as mj

        model = mj.MjModel.from_xml_path(str(model_path))
    except Exception:
        return False
    return all(mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, name) >= 0 for name in body_names)


def retarget_gvhmr_to_mindbot(args: argparse.Namespace) -> dict[str, Path]:
    import general_motion_retargeting.params as gmr_params
    from general_motion_retargeting import GeneralMotionRetargeting as GMR
    from general_motion_retargeting.utils.smpl import get_gvhmr_data_offline_fast, load_gvhmr_pred_file

    from .gmr_registration import register_mindbot

    spec = load_official_spec()
    assert_expected_controlled_joints(spec)
    limits = spec.joint_limits
    joint_names = list(CONTROLLED_JOINT_NAMES)
    lower, upper, velocity = limits_arrays(joint_names, limits)
    default_positions = np.zeros(len(joint_names), dtype=float)

    robot_model = _ensure_model_exists(force=args.rebuild_model)
    register_mindbot(gmr_params, robot_model, repo_path("configs", "smplx_to_mindbot.json"))

    body_model_root = Path(args.smplx_body_models) if args.smplx_body_models else repo_path("third_party", "GMR", "assets", "body_models")
    smplx_data, body_model, smplx_output, actual_human_height = load_gvhmr_pred_file(args.gvhmr_output, body_model_root)
    human_frames, aligned_fps = get_gvhmr_data_offline_fast(
        smplx_data,
        body_model,
        smplx_output,
        tgt_fps=args.target_fps,
    )
    start = max(args.start_frame, 0)
    end = len(human_frames) if args.end_frame is None else min(args.end_frame, len(human_frames))
    if start >= end:
        raise ValueError(f"Invalid frame range: start={start}, end={end}")
    human_frames = human_frames[start:end]
    human_frames, transform_report = transform_human_frames_to_mindbot_workspace(human_frames, robot_model)

    retarget = GMR(
        actual_human_height=None,
        src_human="smplx",
        tgt_robot=ROBOT_NAME,
        verbose=args.verbose,
        use_velocity_limit=True,
    )
    raw_rows: list[list[float]] = []
    for frame in human_frames:
        qpos = retarget.retarget(frame)
        raw_rows.append([_qpos_joint_value(retarget.model, qpos, name) for name in joint_names])

    raw = np.asarray(raw_rows, dtype=float)
    waist_index = joint_names.index("waist_joint")
    if args.waist_mode == "locked":
        raw[:, waist_index] = 0.0
        waist_note = "waist_joint is locked at 0.0 rad; monocular GVHMR global yaw is unstable for this fixed-base waist."
    else:
        raw[:, waist_index] = extract_yaw_from_human_frames(
            human_frames,
            "spine3",
            (limits["waist_joint"].lower, limits["waist_joint"].upper),
            zero_initial=True,
        )
        waist_note = "waist_joint is overridden from zero-initialized SMPL-X spine3 yaw, then unwrapped and clamped."
    timestamps = np.arange(len(raw), dtype=float) / float(aligned_fps)
    config = _load_filter_config(repo_path("configs", "filters.yaml"))
    filtered = filter_joint_trajectory(raw, timestamps, lower, upper, velocity, default_positions, config)

    validation = validate_motion(
        joint_names,
        filtered,
        timestamps,
        limits,
        velocity_margin=float(config.get("limits", {}).get("velocity_margin", 1.0)),
    )
    report = {
        "ok": validation["ok"],
        "validation": validation,
        "robot": ROBOT_NAME,
        "robot_model": relative_to_repo(robot_model),
        "source_gvhmr_file": relative_to_repo(args.gvhmr_output),
        "source_video": relative_to_repo(args.source_video) if args.source_video else "",
        "frames": {"start": start, "end": end, "count": len(raw)},
        "fps": float(aligned_fps),
        "actual_human_height": float(actual_human_height),
        "waist_mode": args.waist_mode,
        "mindbot_frame_transform": transform_report.to_json(),
        "gmr_dof_order": retarget.robot_dof_names,
        "notes": [
            "GVHMR/SMPL-X frames are converted into the fixed-base MindBot arm workspace before GMR IK.",
            "GMR height scaling is disabled after workspace normalization.",
            waist_note,
            "wheel/base translation commands are not emitted in this stage.",
        ],
    }

    output_dir = Path(args.output_dir)
    files = write_motion_bundle(
        output_dir,
        joint_names=joint_names,
        raw_joint_positions=raw,
        joint_positions=filtered,
        timestamps=timestamps,
        fps=float(aligned_fps),
        source_video=args.source_video,
        source_gvhmr_file=args.gvhmr_output,
        robot_model=robot_model,
        gmr_commit=_git_commit(repo_path("third_party", "GMR")),
        gvhmr_commit=_git_commit(repo_path("third_party", "GVHMR")),
        report=report,
    )
    if args.preview:
        report_path = files["report"]
        preview_path = output_dir / "retarget_preview.mp4"
        try:
            from .preview import create_mujoco_preview

            create_mujoco_preview(files["motion"], preview_path)
            report_data = json.loads(report_path.read_text(encoding="utf-8"))
            report_data.setdefault("files", {})["preview"] = relative_to_repo(preview_path)
            report_data["preview_status"] = "ok"
            report_path.write_text(json.dumps(report_data, indent=2, sort_keys=True), encoding="utf-8")
        except Exception as exc:
            report_data = json.loads(report_path.read_text(encoding="utf-8"))
            report_data["preview_status"] = f"failed: {exc}"
            report_path.write_text(json.dumps(report_data, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"motion": relative_to_repo(files["motion"]), "ok": validation["ok"]}, indent=2))
    return files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retarget GVHMR hmr4d_results.pt to MindBot joint motion.")
    parser.add_argument("--gvhmr-output", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source-video", type=Path, default=None)
    parser.add_argument("--robot", default=ROBOT_NAME, choices=[ROBOT_NAME])
    parser.add_argument("--target-fps", type=int, default=30)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--end-frame", type=int, default=None)
    parser.add_argument("--smplx-body-models", type=Path, default=None)
    parser.add_argument("--rebuild-model", action="store_true")
    parser.add_argument(
        "--waist-mode",
        choices=["locked", "spine_yaw"],
        default="locked",
        help="How to drive waist_joint. The default locks the waist because single-camera global yaw is noisy.",
    )
    parser.add_argument("--preview", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    retarget_gvhmr_to_mindbot(parse_args())


if __name__ == "__main__":
    main()
