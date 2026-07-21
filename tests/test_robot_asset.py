from m_c_video_to_robot.robot_asset import CONTROLLED_JOINT_NAMES, assert_expected_controlled_joints, load_official_spec


def test_official_robot_has_expected_controlled_joints():
    spec = load_official_spec()
    assert_expected_controlled_joints(spec)
    assert len(CONTROLLED_JOINT_NAMES) == 13
    assert CONTROLLED_JOINT_NAMES[0] == "waist_joint"
