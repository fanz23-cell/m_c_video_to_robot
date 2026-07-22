from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial.transform import Rotation as Rotation


BVH_COORDINATE_TRANSFORMS: dict[str, np.ndarray] = {
    "y_up_z_forward": np.asarray([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0]], dtype=float),
    "y_up_minus_z_forward": np.asarray([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]], dtype=float),
    "z_up_y_forward": np.eye(3, dtype=float),
    "z_up_minus_y_forward": np.asarray([[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]], dtype=float),
}


@dataclass
class BvhJoint:
    name: str
    parent: int
    offset: np.ndarray
    channels: list[str]


@dataclass
class BvhMotion:
    joints: list[BvhJoint]
    frames: np.ndarray
    frame_time: float
    channel_refs: list[tuple[int, str]]

    @property
    def fps(self) -> float:
        return 1.0 / self.frame_time if self.frame_time > 0.0 else 30.0

    @property
    def joint_names(self) -> list[str]:
        return [joint.name for joint in self.joints]


CANONICAL_CANDIDATES: dict[str, tuple[str, ...]] = {
    "pelvis": ("Hips", "Hip", "Pelvis", "Root", "root"),
    "spine1": ("Spine", "Spine1", "LowerBack", "abdomen"),
    "spine2": ("Spine1", "Spine2", "Chest", "Spine"),
    "spine3": ("Spine2", "Spine3", "Chest", "UpperChest", "Neck", "Spine1", "Spine"),
    "left_shoulder": ("LeftArm", "LeftUpArm", "LeftShoulder", "lShldr", "LShoulder", "Shoulder_L"),
    "left_elbow": ("LeftForeArm", "LeftElbow", "LeftLowerArm", "lForeArm", "LElbow", "ForeArm_L"),
    "left_wrist": ("LeftHand", "LeftWrist", "lHand", "LWrist", "Hand_L"),
    "right_shoulder": ("RightArm", "RightUpArm", "RightShoulder", "rShldr", "RShoulder", "Shoulder_R"),
    "right_elbow": ("RightForeArm", "RightElbow", "RightLowerArm", "rForeArm", "RElbow", "ForeArm_R"),
    "right_wrist": ("RightHand", "RightWrist", "rHand", "RWrist", "Hand_R"),
    "left_hip": ("LeftUpLeg", "LeftHip", "LeftLeg", "lThigh", "LHip", "UpLeg_L"),
    "right_hip": ("RightUpLeg", "RightHip", "RightLeg", "rThigh", "RHip", "UpLeg_R"),
}


def _normal_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _add_joint(joints: list[BvhJoint], name: str, parent: int) -> int:
    joints.append(BvhJoint(name=name, parent=parent, offset=np.zeros(3, dtype=float), channels=[]))
    return len(joints) - 1


def read_bvh(path: str | Path) -> BvhMotion:
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    joints: list[BvhJoint] = []
    channel_refs: list[tuple[int, str]] = []
    stack: list[int] = []
    pending_joint: int | None = None
    in_end_site = False
    end_site_depth = 0
    motion_start = None
    expected_frames = None
    frame_time = None

    for line_no, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue
        if line == "MOTION":
            motion_start = line_no + 1
            break
        if in_end_site:
            if "{" in line:
                end_site_depth += 1
            if "}" in line:
                end_site_depth -= 1
                if end_site_depth <= 0:
                    in_end_site = False
            continue
        if line.startswith("End Site"):
            in_end_site = True
            end_site_depth = 0
            continue
        if line.startswith("ROOT ") or line.startswith("JOINT "):
            _, name = line.split(maxsplit=1)
            parent = stack[-1] if stack else -1
            pending_joint = _add_joint(joints, name, parent)
            continue
        if line == "{":
            if pending_joint is not None:
                stack.append(pending_joint)
                pending_joint = None
            continue
        if line == "}":
            if stack:
                stack.pop()
            continue
        if line.startswith("OFFSET"):
            if not stack:
                raise ValueError(f"OFFSET appears outside a joint at line {line_no + 1}")
            values = [float(part) for part in line.split()[1:4]]
            if len(values) != 3:
                raise ValueError(f"Invalid OFFSET at line {line_no + 1}: {raw_line}")
            joints[stack[-1]].offset = np.asarray(values, dtype=float)
            continue
        if line.startswith("CHANNELS"):
            if not stack:
                raise ValueError(f"CHANNELS appears outside a joint at line {line_no + 1}")
            parts = line.split()
            count = int(parts[1])
            channels = parts[2 : 2 + count]
            if len(channels) != count:
                raise ValueError(f"Invalid CHANNELS at line {line_no + 1}: {raw_line}")
            joints[stack[-1]].channels = channels
            channel_refs.extend((stack[-1], channel) for channel in channels)

    if motion_start is None:
        raise ValueError(f"BVH file is missing MOTION section: {path}")
    if not joints:
        raise ValueError(f"BVH file has no joints: {path}")

    frame_rows: list[list[float]] = []
    for raw_line in lines[motion_start:]:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("Frames:"):
            expected_frames = int(line.split(":", maxsplit=1)[1].strip())
            continue
        if line.startswith("Frame Time:"):
            frame_time = float(line.split(":", maxsplit=1)[1].strip())
            continue
        values = [float(part) for part in line.split()]
        if len(values) != len(channel_refs):
            raise ValueError(f"Expected {len(channel_refs)} motion values, got {len(values)} in line: {raw_line[:120]}")
        frame_rows.append(values)

    if frame_time is None:
        raise ValueError(f"BVH file is missing Frame Time: {path}")
    if expected_frames is not None and expected_frames != len(frame_rows):
        raise ValueError(f"BVH Frames header says {expected_frames}, but parsed {len(frame_rows)} rows from {path}")

    return BvhMotion(
        joints=joints,
        frames=np.asarray(frame_rows, dtype=float),
        frame_time=float(frame_time),
        channel_refs=channel_refs,
    )


def _local_rotation_from_channels(channels: list[str], values: dict[str, float]) -> Rotation:
    rotation = Rotation.identity()
    for channel in channels:
        if not channel.endswith("rotation"):
            continue
        axis = channel[0].lower()
        rotation = rotation * Rotation.from_euler(axis, values[channel], degrees=True)
    return rotation


def _fk_frame(motion: BvhMotion, row: np.ndarray, *, scale: float) -> tuple[np.ndarray, np.ndarray]:
    local_pos = np.stack([joint.offset * scale for joint in motion.joints], axis=0)
    local_rot = [Rotation.identity() for _ in motion.joints]
    channel_values: list[dict[str, float]] = [dict() for _ in motion.joints]

    for value, (joint_idx, channel) in zip(row, motion.channel_refs):
        channel_values[joint_idx][channel] = float(value)
        if channel.endswith("position"):
            axis = "XYZ".index(channel[0])
            local_pos[joint_idx, axis] += float(value) * scale

    for idx, joint in enumerate(motion.joints):
        local_rot[idx] = _local_rotation_from_channels(joint.channels, channel_values[idx])

    global_pos = np.zeros_like(local_pos)
    global_rot: list[Rotation] = [Rotation.identity() for _ in motion.joints]
    for idx, joint in enumerate(motion.joints):
        if joint.parent < 0:
            global_pos[idx] = local_pos[idx]
            global_rot[idx] = local_rot[idx]
            continue
        parent_rot = global_rot[joint.parent]
        global_pos[idx] = global_pos[joint.parent] + parent_rot.apply(local_pos[idx])
        global_rot[idx] = parent_rot * local_rot[idx]
    global_quat_wxyz = np.stack([rotation.as_quat(scalar_first=True) for rotation in global_rot], axis=0)
    return global_pos, global_quat_wxyz


def _find_joint(name_to_index: dict[str, int], canonical_name: str) -> int | None:
    for candidate in CANONICAL_CANDIDATES[canonical_name]:
        normalized = _normal_name(candidate)
        if normalized in name_to_index:
            return name_to_index[normalized]
    suffixes = tuple(_normal_name(candidate) for candidate in CANONICAL_CANDIDATES[canonical_name])
    for normalized, index in name_to_index.items():
        if normalized.endswith(suffixes):
            return index
    return None


def _resample_indices(frame_count: int, source_fps: float, target_fps: float | None) -> tuple[np.ndarray, float]:
    if target_fps is None or target_fps <= 0.0 or abs(source_fps - target_fps) < 1.0e-3:
        return np.arange(frame_count), float(source_fps)
    duration = frame_count / float(source_fps)
    target_count = max(1, int(round(duration * target_fps)))
    times = np.arange(target_count, dtype=float) / float(target_fps)
    indices = np.clip(np.round(times * source_fps).astype(int), 0, frame_count - 1)
    return indices, float(target_fps)


def load_bvh_human_frames(
    path: str | Path,
    *,
    target_fps: float | None = 30.0,
    scale: float = 0.01,
    coordinate_mode: str = "y_up_z_forward",
    start_frame: int = 0,
    end_frame: int | None = None,
) -> tuple[list[dict[str, tuple[np.ndarray, np.ndarray]]], float, dict[str, Any]]:
    motion = read_bvh(path)
    if coordinate_mode not in BVH_COORDINATE_TRANSFORMS:
        raise ValueError(f"Unknown coordinate_mode {coordinate_mode!r}; expected one of {sorted(BVH_COORDINATE_TRANSFORMS)}")
    transform = BVH_COORDINATE_TRANSFORMS[coordinate_mode]
    name_to_index = {_normal_name(name): idx for idx, name in enumerate(motion.joint_names)}
    mapping = {canonical: _find_joint(name_to_index, canonical) for canonical in CANONICAL_CANDIDATES}

    required = ("left_shoulder", "left_elbow", "left_wrist", "right_shoulder", "right_elbow", "right_wrist")
    missing = [name for name in required if mapping[name] is None]
    if missing:
        available = ", ".join(motion.joint_names)
        raise ValueError(f"BVH is missing required upper-body joints {missing}. Available joints: {available}")

    frame_start = max(0, int(start_frame))
    frame_end = motion.frames.shape[0] if end_frame is None else min(int(end_frame), motion.frames.shape[0])
    if frame_start >= frame_end:
        raise ValueError(f"Invalid BVH frame range: start={frame_start}, end={frame_end}")
    source_indices, fps = _resample_indices(frame_end - frame_start, motion.fps, target_fps)
    source_indices = source_indices + frame_start

    frames: list[dict[str, tuple[np.ndarray, np.ndarray]]] = []
    identity = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=float)
    for row_index in source_indices:
        global_pos, _global_quat = _fk_frame(motion, motion.frames[int(row_index)], scale=scale)
        frame: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for canonical, index in mapping.items():
            if index is None:
                continue
            frame[canonical] = (transform @ global_pos[index], identity)
        if "spine3" not in frame:
            left = frame["left_shoulder"][0]
            right = frame["right_shoulder"][0]
            frame["spine3"] = ((left + right) * 0.5, identity)
        frames.append(frame)

    report = {
        "source_joint_names": motion.joint_names,
        "source_fps": motion.fps,
        "output_fps": fps,
        "scale": scale,
        "coordinate_mode": coordinate_mode,
        "canonical_joint_map": {name: None if idx is None else motion.joint_names[idx] for name, idx in mapping.items()},
        "frames": {"start": frame_start, "end": frame_end, "count": len(frames)},
    }
    return frames, fps, report
