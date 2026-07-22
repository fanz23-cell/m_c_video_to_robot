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


def extract_yaw_from_human_frames(
    frames: list[dict[str, Any]],
    body_name: str,
    limits: tuple[float, float],
    *,
    zero_initial: bool = False,
) -> np.ndarray:
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
    if zero_initial and len(yaw_series) > 0:
        yaw_series = yaw_series - yaw_series[0]
    return np.clip(yaw_series, limits[0], limits[1])


def _interpolate_nonfinite_1d(values: np.ndarray) -> np.ndarray:
    out = np.asarray(values, dtype=float).copy()
    valid = np.isfinite(out)
    if valid.all():
        return out
    if not valid.any():
        return np.zeros_like(out)
    indices = np.arange(len(out))
    out[~valid] = np.interp(indices[~valid], indices[valid], out[valid])
    return out


def _odd_window(window_length: int, sample_count: int) -> int:
    window = max(3, int(window_length))
    if window % 2 == 0:
        window += 1
    if window > sample_count:
        window = sample_count if sample_count % 2 == 1 else sample_count - 1
    return max(window, 3)


def _smooth_1d(values: np.ndarray, *, window_length: int, polyorder: int) -> np.ndarray:
    if window_length <= 1 or values.shape[0] < 3:
        return values.copy()
    window = _odd_window(window_length, values.shape[0])
    try:
        from scipy.signal import savgol_filter

        return savgol_filter(values, window_length=window, polyorder=min(polyorder, window - 1), mode="interp")
    except Exception:
        kernel = np.ones(window, dtype=float) / float(window)
        padded = np.pad(values, (window // 2, window // 2), mode="edge")
        return np.convolve(padded, kernel, mode="valid")


def _body_axis_angle(
    frame: dict[str, Any],
    left_name: str,
    right_name: str,
    transform: np.ndarray,
) -> tuple[float, float] | None:
    if left_name not in frame or right_name not in frame:
        return None
    left = transform @ np.asarray(frame[left_name][0], dtype=float)
    right = transform @ np.asarray(frame[right_name][0], dtype=float)
    axis = left - right
    axis[2] = 0.0
    norm = float(np.linalg.norm(axis[:2]))
    if norm <= 1.0e-6:
        return None
    return float(np.arctan2(axis[1], axis[0])), norm


def extract_torso_heading_yaw_from_human_frames(
    frames: list[dict[str, Any]],
    limits: tuple[float, float],
    *,
    position_transform: np.ndarray | None = None,
    zero_initial: bool = True,
    smooth_window: int = 31,
    smooth_polyorder: int = 2,
    deadband: float = 0.05,
) -> np.ndarray:
    """Estimate stable waist yaw from shoulder and hip left-right body axes."""

    transform = np.eye(3, dtype=float) if position_transform is None else np.asarray(position_transform, dtype=float)
    yaw_values: list[float] = []
    for frame in frames:
        candidates = [
            _body_axis_angle(frame, "left_shoulder", "right_shoulder", transform),
            _body_axis_angle(frame, "left_hip", "right_hip", transform),
        ]
        weighted_sin = 0.0
        weighted_cos = 0.0
        total_weight = 0.0
        for candidate, body_weight in zip(candidates, (0.6, 0.4), strict=True):
            if candidate is None:
                continue
            angle, axis_norm = candidate
            weight = body_weight * axis_norm
            weighted_sin += weight * float(np.sin(angle))
            weighted_cos += weight * float(np.cos(angle))
            total_weight += weight
        if total_weight <= 1.0e-9:
            yaw_values.append(np.nan)
        else:
            yaw_values.append(float(np.arctan2(weighted_sin, weighted_cos)))

    yaw_series = np.unwrap(_interpolate_nonfinite_1d(np.asarray(yaw_values, dtype=float)))
    yaw_series = _smooth_1d(yaw_series, window_length=smooth_window, polyorder=smooth_polyorder)
    if zero_initial and len(yaw_series) > 0:
        yaw_series = yaw_series - yaw_series[0]
    if deadband > 0.0:
        magnitude = np.abs(yaw_series)
        yaw_series = np.sign(yaw_series) * np.maximum(magnitude - float(deadband), 0.0)
    return np.clip(yaw_series, limits[0], limits[1])
