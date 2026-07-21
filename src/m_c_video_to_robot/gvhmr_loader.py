from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial.transform import Rotation as Rotation


def find_gvhmr_result(output_root: str | Path, video_stem: str | None = None) -> Path:
    root = Path(output_root)
    candidates: list[Path] = []
    if root.is_file():
        return root
    if video_stem is not None:
        candidates.append(root / video_stem / "hmr4d_results.pt")
    candidates.append(root / "hmr4d_results.pt")
    candidates.extend(root.glob("*/hmr4d_results.pt"))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find hmr4d_results.pt under {root}")


def extract_yaw_from_human_frames(frames: list[dict[str, Any]], body_name: str, limits: tuple[float, float]) -> np.ndarray:
    """Extract global yaw from a SMPL-X body quaternion in wxyz order."""

    yaw_values: list[float] = []
    for frame in frames:
        if body_name not in frame:
            raise KeyError(f"GVHMR/GMR human frame is missing body {body_name!r}")
        quat_wxyz = np.asarray(frame[body_name][1], dtype=float)
        quat_xyzw = quat_wxyz[[1, 2, 3, 0]]
        yaw = Rotation.from_quat(quat_xyzw).as_euler("zyx", degrees=False)[0]
        yaw_values.append(float(yaw))
    yaw_series = np.unwrap(np.asarray(yaw_values, dtype=float))
    return np.clip(yaw_series, limits[0], limits[1])
