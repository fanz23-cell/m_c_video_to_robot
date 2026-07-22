from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .filters import filter_joint_trajectory
from .gvhmr_loader import extract_torso_heading_yaw_from_human_frames, extract_yaw_from_human_frames
from .human_frame_transform import HUMAN_TO_MINDBOT, transform_human_frames_to_mindbot_workspace
from .limits import limits_arrays, validate_motion
from .motion_format import write_motion_bundle
from .paths import relative_to_repo, repo_path
from .robot_asset import CONTROLLED_JOINT_NAMES, ROBOT_NAME, assert_expected_controlled_joints, generated_model_path, load_official_spec

WAIST_MODE_CHOICES = ("torso_heading", "locked", "spine_yaw")


def git_commit(path: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def load_filter_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def qpos_joint_value(model, qpos: np.ndarray, joint_name: str) -> float:
    import mujoco as mj

    joint_id = mj.mj_name2id(model, mj.mjtObj.mjOBJ_JOINT, joint_name)
    if joint_id < 0:
        raise KeyError(f"MuJoCo model is missing joint {joint_name!r}")
    qpos_adr = int(model.jnt_qposadr[joint_id])
    return float(qpos[qpos_adr])


def ensure_model_exists(force: bool = False) -> Path:
    model_path = generated_model_path(prefer_xml=True)
    if model_path.exists() and not force and model_has_required_bodies(model_path, ("left_arm_tcp", "right_arm_tcp")):
        return model_path
    from .build_model import build_model

    return build_model(force=True)


def model_has_required_bodies(model_path: Path, body_names: tuple[str, ...]) -> bool:
    try:
        import mujoco as mj

        model = mj.MjModel.from_xml_path(str(model_path))
    except Exception:
        return False
    return all(mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, name) >= 0 for name in body_names)


def _waist_override(
    *,
    waist_mode: str,
    source_human_frames: list[dict[str, Any]],
    transformed_human_frames: list[dict[str, Any]],
    limits: Any,
) -> tuple[np.ndarray, str]:
    if waist_mode == "torso_heading":
        waist = extract_torso_heading_yaw_from_human_frames(
            source_human_frames,
            (limits["waist_joint"].lower, limits["waist_joint"].upper),
            position_transform=HUMAN_TO_MINDBOT,
        )
        return waist, "waist_joint follows a smoothed torso heading estimated from shoulder and hip geometry."
    if waist_mode == "locked":
        return np.zeros(len(source_human_frames), dtype=float), (
            "waist_joint is locked at 0.0 rad for arm-only debugging."
        )
    if waist_mode == "spine_yaw":
        waist = extract_yaw_from_human_frames(
            transformed_human_frames,
            "spine3",
            (limits["waist_joint"].lower, limits["waist_joint"].upper),
            zero_initial=True,
        )
        return waist, "waist_joint is overridden from zero-initialized spine3 yaw, then unwrapped and clamped."
    raise ValueError(f"Unsupported waist_mode {waist_mode!r}; expected one of {WAIST_MODE_CHOICES}")


def retarget_human_frames_to_mindbot(
    *,
    human_frames: list[dict[str, Any]],
    fps: float,
    output_dir: str | Path,
    source_kind: str,
    source_motion_file: str | Path,
    source_video: str | Path | None = None,
    actual_human_height: float | None = None,
    waist_mode: str = "torso_heading",
    rebuild_model: bool = False,
    preview: bool = True,
    verbose: bool = False,
    frame_start: int = 0,
    frame_end: int | None = None,
    source_report: dict[str, Any] | None = None,
) -> dict[str, Path]:
    import general_motion_retargeting.params as gmr_params
    from general_motion_retargeting import GeneralMotionRetargeting as GMR

    from .gmr_registration import register_mindbot

    if not human_frames:
        raise ValueError("No human frames were provided for retargeting.")

    spec = load_official_spec()
    assert_expected_controlled_joints(spec)
    limits = spec.joint_limits
    joint_names = list(CONTROLLED_JOINT_NAMES)
    lower, upper, velocity = limits_arrays(joint_names, limits)
    default_positions = np.zeros(len(joint_names), dtype=float)

    robot_model = ensure_model_exists(force=rebuild_model)
    register_mindbot(gmr_params, robot_model, repo_path("configs", "smplx_to_mindbot.json"))

    transformed_human_frames, transform_report = transform_human_frames_to_mindbot_workspace(human_frames, robot_model)
    waist_yaw, waist_note = _waist_override(
        waist_mode=waist_mode,
        source_human_frames=human_frames,
        transformed_human_frames=transformed_human_frames,
        limits=limits,
    )

    retarget = GMR(
        actual_human_height=None,
        src_human="smplx",
        tgt_robot=ROBOT_NAME,
        verbose=verbose,
        use_velocity_limit=True,
    )
    raw_rows: list[list[float]] = []
    for frame in transformed_human_frames:
        qpos = retarget.retarget(frame)
        raw_rows.append([qpos_joint_value(retarget.model, qpos, name) for name in joint_names])

    raw = np.asarray(raw_rows, dtype=float)
    raw[:, joint_names.index("waist_joint")] = waist_yaw
    timestamps = np.arange(len(raw), dtype=float) / float(fps)
    config = load_filter_config(repo_path("configs", "filters.yaml"))
    filtered = filter_joint_trajectory(raw, timestamps, lower, upper, velocity, default_positions, config)

    validation = validate_motion(
        joint_names,
        filtered,
        timestamps,
        limits,
        velocity_margin=float(config.get("limits", {}).get("velocity_margin", 1.0)),
    )
    source_motion_file = Path(source_motion_file)
    report = {
        "ok": validation["ok"],
        "validation": validation,
        "robot": ROBOT_NAME,
        "robot_model": relative_to_repo(robot_model),
        "source_kind": source_kind,
        "source_motion_file": relative_to_repo(source_motion_file),
        "source_gvhmr_file": relative_to_repo(source_motion_file) if source_kind == "gvhmr" else "",
        "source_video": relative_to_repo(source_video) if source_video else "",
        "frames": {"start": frame_start, "end": frame_end if frame_end is not None else frame_start + len(raw), "count": len(raw)},
        "fps": float(fps),
        "actual_human_height": None if actual_human_height is None else float(actual_human_height),
        "waist_mode": waist_mode,
        "source_report": source_report or {},
        "mindbot_frame_transform": transform_report.to_json(),
        "gmr_dof_order": retarget.robot_dof_names,
        "notes": [
            f"{source_kind} frames are converted into the fixed-base MindBot arm workspace before GMR IK.",
            "GMR height scaling is disabled after workspace normalization.",
            waist_note,
            "wheel/base translation commands are not emitted in this stage.",
        ],
    }

    output_dir = Path(output_dir)
    files = write_motion_bundle(
        output_dir,
        joint_names=joint_names,
        raw_joint_positions=raw,
        joint_positions=filtered,
        timestamps=timestamps,
        fps=float(fps),
        source_video=source_video,
        source_gvhmr_file=source_motion_file if source_kind == "gvhmr" else None,
        source_motion_file=source_motion_file,
        source_motion_kind=source_kind,
        robot_model=robot_model,
        gmr_commit=git_commit(repo_path("third_party", "GMR")),
        gvhmr_commit=git_commit(repo_path("third_party", "GVHMR")),
        report=report,
    )
    if preview:
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
