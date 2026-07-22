import pytest

from m_c_video_to_robot.retarget import _ensure_model_exists
from m_c_video_to_robot.robot_asset import CONTROLLED_JOINT_NAMES, assert_expected_controlled_joints, load_official_spec


def test_official_robot_has_expected_controlled_joints():
    spec = load_official_spec()
    assert_expected_controlled_joints(spec)
    assert len(CONTROLLED_JOINT_NAMES) == 13
    assert CONTROLLED_JOINT_NAMES[0] == "waist_joint"


def test_generated_gmr_model_exposes_tcp_task_frames():
    mj = pytest.importorskip("mujoco")
    model_path = _ensure_model_exists()
    model = mj.MjModel.from_xml_path(str(model_path))
    assert mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, "left_arm_tcp") >= 0
    assert mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, "right_arm_tcp") >= 0
