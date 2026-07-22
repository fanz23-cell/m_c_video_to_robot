from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial.transform import Rotation as Rotation


HUMAN_TO_MINDBOT = np.asarray(
    [
        [0.0, 1.0, 0.0],
        [-1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0],
    ],
    dtype=float,
)
HUMAN_TO_MINDBOT_ROTATION = Rotation.from_matrix(HUMAN_TO_MINDBOT)


@dataclass(frozen=True)
class ArmScale:
    upper: float
    forearm: float


@dataclass(frozen=True)
class MindbotFrameTransformReport:
    coordinate_map: str
    left_arm_scale: ArmScale
    right_arm_scale: ArmScale
    robot_reference_bodies: dict[str, str]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def _body_position(model, data, name: str) -> np.ndarray:
    import mujoco as mj

    body_id = mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, name)
    if body_id < 0:
        raise RuntimeError(f"Generated MindBot GMR model is missing body {name!r}")
    return np.asarray(data.xpos[body_id], dtype=float).copy()


def _reference_positions(robot_model: Path) -> dict[str, np.ndarray]:
    import mujoco as mj

    model = mj.MjModel.from_xml_path(str(robot_model))
    data = mj.MjData(model)
    mj.mj_forward(model, data)
    names = (
        "waist_link",
        "left_arm_link_1",
        "left_arm_link_4",
        "left_arm_tcp",
        "right_arm_link_1",
        "right_arm_link_4",
        "right_arm_tcp",
    )
    return {name: _body_position(model, data, name) for name in names}


def _median_segment_length(frames: list[dict[str, Any]], start: str, end: str) -> float:
    lengths = [float(np.linalg.norm(np.asarray(frame[end][0]) - np.asarray(frame[start][0]))) for frame in frames]
    median = float(np.median(lengths))
    if median <= 1.0e-6:
        raise ValueError(f"Invalid SMPL-X segment length for {start}->{end}: {median}")
    return median


def _arm_scale(
    frames: list[dict[str, Any]],
    reference: dict[str, np.ndarray],
    *,
    side: str,
) -> ArmScale:
    shoulder = f"{side}_shoulder"
    elbow = f"{side}_elbow"
    wrist = f"{side}_wrist"
    shoulder_body = f"{side}_arm_link_1"
    elbow_body = f"{side}_arm_link_4"
    wrist_body = f"{side}_arm_tcp"
    robot_upper = float(np.linalg.norm(reference[elbow_body] - reference[shoulder_body]))
    robot_forearm = float(np.linalg.norm(reference[wrist_body] - reference[elbow_body]))
    return ArmScale(
        upper=robot_upper / _median_segment_length(frames, shoulder, elbow),
        forearm=robot_forearm / _median_segment_length(frames, elbow, wrist),
    )


def _rotate_quat_wxyz(quat_wxyz: np.ndarray) -> np.ndarray:
    return (HUMAN_TO_MINDBOT_ROTATION * Rotation.from_quat(quat_wxyz, scalar_first=True)).as_quat(scalar_first=True)


def _source_rotation(frame: dict[str, Any], body_name: str) -> np.ndarray:
    return _rotate_quat_wxyz(np.asarray(frame[body_name][1], dtype=float))


def _arm_points(
    frame: dict[str, Any],
    reference: dict[str, np.ndarray],
    scale: ArmScale,
    *,
    side: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    shoulder_name = f"{side}_shoulder"
    elbow_name = f"{side}_elbow"
    wrist_name = f"{side}_wrist"
    shoulder = np.asarray(frame[shoulder_name][0], dtype=float)
    elbow = np.asarray(frame[elbow_name][0], dtype=float)
    wrist = np.asarray(frame[wrist_name][0], dtype=float)
    robot_shoulder = reference[f"{side}_arm_link_1"]

    upper_vector = HUMAN_TO_MINDBOT @ (elbow - shoulder)
    forearm_vector = HUMAN_TO_MINDBOT @ (wrist - elbow)
    robot_elbow = robot_shoulder + scale.upper * upper_vector
    robot_wrist = robot_elbow + scale.forearm * forearm_vector
    return robot_shoulder, robot_elbow, robot_wrist


def transform_human_frames_to_mindbot_workspace(
    frames: list[dict[str, Any]],
    robot_model: str | Path,
) -> tuple[list[dict[str, tuple[np.ndarray, np.ndarray]]], MindbotFrameTransformReport]:
    """Convert GVHMR/SMPL-X frames into the fixed-base MindBot arm workspace."""

    if not frames:
        raise ValueError("No human frames to transform.")

    reference = _reference_positions(Path(robot_model))
    left_scale = _arm_scale(frames, reference, side="left")
    right_scale = _arm_scale(frames, reference, side="right")
    transformed: list[dict[str, tuple[np.ndarray, np.ndarray]]] = []

    for frame in frames:
        left_shoulder, left_elbow, left_wrist = _arm_points(frame, reference, left_scale, side="left")
        right_shoulder, right_elbow, right_wrist = _arm_points(frame, reference, right_scale, side="right")
        transformed.append(
            {
                "spine3": (reference["waist_link"], _source_rotation(frame, "spine3")),
                "left_shoulder": (left_shoulder, _source_rotation(frame, "left_shoulder")),
                "left_elbow": (left_elbow, _source_rotation(frame, "left_elbow")),
                "left_wrist": (left_wrist, _source_rotation(frame, "left_wrist")),
                "right_shoulder": (right_shoulder, _source_rotation(frame, "right_shoulder")),
                "right_elbow": (right_elbow, _source_rotation(frame, "right_elbow")),
                "right_wrist": (right_wrist, _source_rotation(frame, "right_wrist")),
            }
        )

    report = MindbotFrameTransformReport(
        coordinate_map="robot_x=human_y, robot_y=-human_x, robot_z=human_z; arms are anchored at MindBot shoulder frames",
        left_arm_scale=left_scale,
        right_arm_scale=right_scale,
        robot_reference_bodies={
            "spine3": "waist_link",
            "left_shoulder": "left_arm_link_1",
            "left_elbow": "left_arm_link_4",
            "left_wrist": "left_arm_tcp",
            "right_shoulder": "right_arm_link_1",
            "right_elbow": "right_arm_link_4",
            "right_wrist": "right_arm_tcp",
        },
    )
    return transformed, report
