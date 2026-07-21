from __future__ import annotations

import numpy as np


def interpolate_nonfinite(values: np.ndarray) -> np.ndarray:
    out = np.asarray(values, dtype=float).copy()
    frames = np.arange(out.shape[0])
    for joint_idx in range(out.shape[1]):
        column = out[:, joint_idx]
        valid = np.isfinite(column)
        if valid.all():
            continue
        if not valid.any():
            out[:, joint_idx] = 0.0
            continue
        out[:, joint_idx] = np.interp(frames, frames[valid], column[valid])
    return out


def _odd_window(window_length: int, sample_count: int) -> int:
    window = max(3, int(window_length))
    if window % 2 == 0:
        window += 1
    if window > sample_count:
        window = sample_count if sample_count % 2 == 1 else sample_count - 1
    return max(window, 3)


def smooth_trajectory(values: np.ndarray, *, method: str, window_length: int, polyorder: int) -> np.ndarray:
    if values.shape[0] < 3:
        return values.copy()
    window = _odd_window(window_length, values.shape[0])
    if method == "savgol":
        try:
            from scipy.signal import savgol_filter

            return savgol_filter(values, window_length=window, polyorder=min(polyorder, window - 1), axis=0, mode="interp")
        except Exception:
            pass
    kernel = np.ones(window, dtype=float) / float(window)
    padded = np.pad(values, ((window // 2, window // 2), (0, 0)), mode="edge")
    smoothed = np.empty_like(values)
    for joint_idx in range(values.shape[1]):
        smoothed[:, joint_idx] = np.convolve(padded[:, joint_idx], kernel, mode="valid")
    return smoothed


def clamp_to_limits(values: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, lower[None, :]), upper[None, :])


def limit_velocity(values: np.ndarray, timestamps: np.ndarray, velocity_limits: np.ndarray) -> np.ndarray:
    out = values.copy()
    if len(out) < 2:
        return out
    for idx in range(1, len(out)):
        dt = max(float(timestamps[idx] - timestamps[idx - 1]), 1.0e-6)
        delta_limit = velocity_limits * dt
        delta = np.clip(out[idx] - out[idx - 1], -delta_limit, delta_limit)
        out[idx] = out[idx - 1] + delta
    return out


def limit_acceleration(values: np.ndarray, timestamps: np.ndarray, acceleration_limit: float | None) -> np.ndarray:
    if acceleration_limit is None or acceleration_limit <= 0.0 or len(values) < 3:
        return values
    out = values.copy()
    for idx in range(2, len(out)):
        dt_prev = max(float(timestamps[idx - 1] - timestamps[idx - 2]), 1.0e-6)
        dt = max(float(timestamps[idx] - timestamps[idx - 1]), 1.0e-6)
        prev_vel = (out[idx - 1] - out[idx - 2]) / dt_prev
        proposed_vel = (out[idx] - out[idx - 1]) / dt
        vel_delta = np.clip(proposed_vel - prev_vel, -acceleration_limit * dt, acceleration_limit * dt)
        out[idx] = out[idx - 1] + (prev_vel + vel_delta) * dt
    return out


def apply_endpoint_transitions(
    values: np.ndarray,
    timestamps: np.ndarray,
    default_positions: np.ndarray,
    *,
    start_seconds: float,
    end_seconds: float,
) -> np.ndarray:
    out = values.copy()
    if len(out) == 0:
        return out
    start_duration = max(start_seconds, 0.0)
    end_duration = max(end_seconds, 0.0)
    if start_duration > 0.0:
        mask = timestamps <= timestamps[0] + start_duration
        for idx in np.where(mask)[0]:
            alpha = (timestamps[idx] - timestamps[0]) / start_duration
            alpha = 3.0 * alpha**2 - 2.0 * alpha**3
            out[idx] = (1.0 - alpha) * default_positions + alpha * out[idx]
    if end_duration > 0.0:
        mask = timestamps >= timestamps[-1] - end_duration
        for idx in np.where(mask)[0]:
            alpha = (timestamps[-1] - timestamps[idx]) / end_duration
            alpha = 3.0 * alpha**2 - 2.0 * alpha**3
            out[idx] = (1.0 - alpha) * default_positions + alpha * out[idx]
    return out


def filter_joint_trajectory(
    raw: np.ndarray,
    timestamps: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    velocity_limits: np.ndarray,
    default_positions: np.ndarray,
    config: dict,
) -> np.ndarray:
    values = interpolate_nonfinite(raw)
    filter_cfg = config.get("filter", {})
    if filter_cfg.get("enabled", True):
        values = smooth_trajectory(
            values,
            method=str(filter_cfg.get("type", "savgol")),
            window_length=int(filter_cfg.get("window_length", 9)),
            polyorder=int(filter_cfg.get("polyorder", 3)),
        )
    values = clamp_to_limits(values, lower, upper)
    limits_cfg = config.get("limits", {})
    margin = float(limits_cfg.get("velocity_margin", 1.0))
    values = limit_velocity(values, timestamps, velocity_limits * margin)
    values = limit_acceleration(values, timestamps, limits_cfg.get("acceleration_limit"))
    transition_cfg = config.get("transition", {})
    values = apply_endpoint_transitions(
        values,
        timestamps,
        default_positions,
        start_seconds=float(transition_cfg.get("start_seconds", 0.0)),
        end_seconds=float(transition_cfg.get("end_seconds", 0.0)),
    )
    return clamp_to_limits(values, lower, upper)
