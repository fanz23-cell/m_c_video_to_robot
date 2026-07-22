from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from .paths import relative_to_repo


def write_motion_bundle(
    output_dir: str | Path,
    *,
    joint_names: list[str],
    raw_joint_positions: np.ndarray,
    joint_positions: np.ndarray,
    timestamps: np.ndarray,
    fps: float,
    source_video: str | Path | None,
    robot_model: str | Path,
    gmr_commit: str,
    gvhmr_commit: str,
    report: dict[str, Any],
    source_gvhmr_file: str | Path | None = None,
    source_motion_file: str | Path | None = None,
    source_motion_kind: str = "",
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    motion_path = out / "mindbot_motion.npz"
    csv_path = out / "joint_trajectory.csv"
    report_path = out / "retarget_report.json"

    source_video_str = "" if source_video is None else relative_to_repo(source_video)
    source_gvhmr_str = "" if source_gvhmr_file is None else relative_to_repo(source_gvhmr_file)
    source_motion = source_motion_file if source_motion_file is not None else source_gvhmr_file
    source_motion_str = "" if source_motion is None else relative_to_repo(source_motion)
    np.savez(
        motion_path,
        joint_names=np.asarray(joint_names, dtype=str),
        joint_positions=np.asarray(joint_positions, dtype=float),
        raw_joint_positions=np.asarray(raw_joint_positions, dtype=float),
        timestamps=np.asarray(timestamps, dtype=float),
        fps=np.asarray(float(fps), dtype=float),
        source_video=np.asarray(source_video_str, dtype=str),
        source_gvhmr_file=np.asarray(source_gvhmr_str, dtype=str),
        source_motion_file=np.asarray(source_motion_str, dtype=str),
        source_motion_kind=np.asarray(source_motion_kind, dtype=str),
        robot_model=np.asarray(relative_to_repo(robot_model), dtype=str),
        gmr_commit=np.asarray(gmr_commit, dtype=str),
        gvhmr_commit=np.asarray(gvhmr_commit, dtype=str),
    )

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", *joint_names])
        for t, row in zip(timestamps, joint_positions):
            writer.writerow([f"{float(t):.9f}", *[f"{float(value):.9f}" for value in row]])

    report = dict(report)
    report["files"] = {
        "motion": relative_to_repo(motion_path),
        "csv": relative_to_repo(csv_path),
        "report": relative_to_repo(report_path),
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return {"motion": motion_path, "csv": csv_path, "report": report_path}


def load_motion(path: str | Path) -> dict[str, Any]:
    data = np.load(path, allow_pickle=False)
    return {
        "joint_names": [str(name) for name in data["joint_names"].tolist()],
        "joint_positions": np.asarray(data["joint_positions"], dtype=float),
        "raw_joint_positions": np.asarray(data["raw_joint_positions"], dtype=float) if "raw_joint_positions" in data else None,
        "timestamps": np.asarray(data["timestamps"], dtype=float),
        "fps": float(np.asarray(data["fps"]).item()),
        "source_video": str(np.asarray(data["source_video"]).item()) if "source_video" in data else "",
        "source_gvhmr_file": str(np.asarray(data["source_gvhmr_file"]).item()) if "source_gvhmr_file" in data else "",
        "source_motion_file": str(np.asarray(data["source_motion_file"]).item()) if "source_motion_file" in data else "",
        "source_motion_kind": str(np.asarray(data["source_motion_kind"]).item()) if "source_motion_kind" in data else "",
        "robot_model": str(np.asarray(data["robot_model"]).item()) if "robot_model" in data else "",
        "gmr_commit": str(np.asarray(data["gmr_commit"]).item()) if "gmr_commit" in data else "",
        "gvhmr_commit": str(np.asarray(data["gvhmr_commit"]).item()) if "gvhmr_commit" in data else "",
    }
