from pathlib import Path

import numpy as np

from m_c_video_to_robot.bvh_loader import load_bvh_human_frames, read_bvh


MINIMAL_BVH = """HIERARCHY
ROOT Hips
{
  OFFSET 0.0 0.0 0.0
  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
  JOINT Spine
  {
    OFFSET 0.0 10.0 0.0
    CHANNELS 3 Zrotation Xrotation Yrotation
    JOINT Chest
    {
      OFFSET 0.0 10.0 0.0
      CHANNELS 3 Zrotation Xrotation Yrotation
      JOINT LeftArm
      {
        OFFSET 10.0 0.0 0.0
        CHANNELS 3 Zrotation Xrotation Yrotation
        JOINT LeftForeArm
        {
          OFFSET 10.0 0.0 0.0
          CHANNELS 3 Zrotation Xrotation Yrotation
          JOINT LeftHand
          {
            OFFSET 10.0 0.0 0.0
            CHANNELS 3 Zrotation Xrotation Yrotation
          }
        }
      }
      JOINT RightArm
      {
        OFFSET -10.0 0.0 0.0
        CHANNELS 3 Zrotation Xrotation Yrotation
        JOINT RightForeArm
        {
          OFFSET -10.0 0.0 0.0
          CHANNELS 3 Zrotation Xrotation Yrotation
          JOINT RightHand
          {
            OFFSET -10.0 0.0 0.0
            CHANNELS 3 Zrotation Xrotation Yrotation
          }
        }
      }
    }
  }
  JOINT LeftUpLeg
  {
    OFFSET 5.0 -10.0 0.0
    CHANNELS 3 Zrotation Xrotation Yrotation
  }
  JOINT RightUpLeg
  {
    OFFSET -5.0 -10.0 0.0
    CHANNELS 3 Zrotation Xrotation Yrotation
  }
}
MOTION
Frames: 2
Frame Time: 0.0333333
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
"""


def _write_bvh(tmp_path: Path) -> Path:
    path = tmp_path / "minimal.bvh"
    path.write_text(MINIMAL_BVH, encoding="utf-8")
    return path


def test_read_bvh_parses_hierarchy_and_motion(tmp_path):
    path = _write_bvh(tmp_path)
    motion = read_bvh(path)

    assert motion.joint_names[0] == "Hips"
    assert "LeftHand" in motion.joint_names
    assert motion.frames.shape == (2, 36)
    assert np.isclose(motion.fps, 30.0, atol=1.0e-3)


def test_load_bvh_human_frames_maps_upper_body(tmp_path):
    path = _write_bvh(tmp_path)

    frames, fps, report = load_bvh_human_frames(path, coordinate_mode="z_up_y_forward", target_fps=30.0)

    assert len(frames) == 2
    assert np.isclose(fps, 30.0, atol=1.0e-3)
    assert report["canonical_joint_map"]["left_wrist"] == "LeftHand"
    for name in ("spine3", "left_shoulder", "left_elbow", "left_wrist", "right_shoulder", "right_elbow", "right_wrist"):
        assert name in frames[0]
