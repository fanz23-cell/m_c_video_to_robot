import numpy as np

from m_c_video_to_robot.gvhmr_loader import extract_torso_heading_yaw_from_human_frames


def _torso_frame(yaw: float) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    axis = np.array([np.cos(yaw), np.sin(yaw), 0.0], dtype=float)
    shoulder_center = np.array([0.0, 0.0, 1.3], dtype=float)
    hip_center = np.array([0.0, 0.0, 0.8], dtype=float)
    quat = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
    return {
        "left_shoulder": (shoulder_center + 0.2 * axis, quat),
        "right_shoulder": (shoulder_center - 0.2 * axis, quat),
        "left_hip": (hip_center + 0.15 * axis, quat),
        "right_hip": (hip_center - 0.15 * axis, quat),
    }


def test_torso_heading_follows_side_turn():
    expected = np.linspace(0.0, np.pi / 2.0, 9)
    frames = [_torso_frame(float(yaw)) for yaw in expected]

    actual = extract_torso_heading_yaw_from_human_frames(
        frames,
        (-np.pi, np.pi),
        smooth_window=0,
        deadband=0.0,
    )

    np.testing.assert_allclose(actual, expected, atol=1.0e-6)


def test_torso_heading_deadband_suppresses_small_wobble():
    frames = [_torso_frame(yaw) for yaw in (0.0, 0.01, -0.01, 0.02)]

    actual = extract_torso_heading_yaw_from_human_frames(
        frames,
        (-np.pi, np.pi),
        smooth_window=0,
        deadband=0.05,
    )

    np.testing.assert_allclose(actual, np.zeros(4), atol=1.0e-6)
