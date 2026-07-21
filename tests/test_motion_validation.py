import numpy as np

from m_c_video_to_robot.limits import validate_motion
from m_c_video_to_robot.robot_asset import CONTROLLED_JOINT_NAMES, load_official_spec


def test_zero_motion_validates_against_official_limits():
    spec = load_official_spec()
    joint_names = list(CONTROLLED_JOINT_NAMES)
    timestamps = np.array([0.0, 1.0 / 30.0, 2.0 / 30.0])
    joint_positions = np.zeros((3, len(joint_names)))
    result = validate_motion(joint_names, joint_positions, timestamps, spec.joint_limits)
    assert result["ok"]
