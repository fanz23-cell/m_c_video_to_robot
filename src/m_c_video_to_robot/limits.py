from __future__ import annotations

from dataclasses import asdict

import numpy as np

from .robot_asset import JointLimit


def limits_arrays(joint_names: list[str] | tuple[str, ...], limits: dict[str, JointLimit]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    lower = np.asarray([limits[name].lower for name in joint_names], dtype=float)
    upper = np.asarray([limits[name].upper for name in joint_names], dtype=float)
    velocity = np.asarray([limits[name].velocity for name in joint_names], dtype=float)
    return lower, upper, velocity


def validate_motion(
    joint_names: list[str] | tuple[str, ...],
    joint_positions: np.ndarray,
    timestamps: np.ndarray,
    limits: dict[str, JointLimit],
    *,
    velocity_margin: float = 1.0,
) -> dict:
    lower, upper, velocity = limits_arrays(joint_names, limits)
    result = {
        "joint_count": len(joint_names),
        "frame_count": int(joint_positions.shape[0]),
        "checks": {},
        "joint_limits": {name: asdict(limits[name]) for name in joint_names},
    }
    checks = result["checks"]
    checks["all_joint_names_have_limits"] = bool(all(name in limits for name in joint_names))
    checks["no_nan"] = bool(not np.isnan(joint_positions).any())
    checks["no_inf"] = bool(np.isfinite(joint_positions).all())
    checks["timestamps_strictly_increasing"] = bool(np.all(np.diff(timestamps) > 0.0)) if len(timestamps) > 1 else True
    below = joint_positions < (lower[None, :] - 1.0e-6)
    above = joint_positions > (upper[None, :] + 1.0e-6)
    checks["within_position_limits"] = bool(not np.any(below | above))
    if len(joint_positions) > 1:
        dt = np.diff(timestamps)[:, None]
        velocities = np.abs(np.diff(joint_positions, axis=0) / np.maximum(dt, 1.0e-6))
        checks["within_velocity_limits"] = bool(not np.any(velocities > velocity[None, :] * velocity_margin + 1.0e-6))
        result["max_abs_velocity"] = {
            name: float(velocities[:, idx].max(initial=0.0)) for idx, name in enumerate(joint_names)
        }
    else:
        checks["within_velocity_limits"] = True
        result["max_abs_velocity"] = {name: 0.0 for name in joint_names}
    checks["left_arm_joint_count"] = bool(sum(name.startswith("left_arm_joint_") for name in joint_names) == 6)
    checks["right_arm_joint_count"] = bool(sum(name.startswith("right_arm_joint_") for name in joint_names) == 6)
    result["ok"] = all(bool(value) for value in checks.values())
    return result
