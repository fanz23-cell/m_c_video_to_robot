from __future__ import annotations

from pathlib import Path
import os

import numpy as np

from .motion_format import load_motion
from .paths import resolve_from_repo


def create_mujoco_preview(motion_path: str | Path, output_path: str | Path, *, width: int = 640, height: int = 480) -> Path:
    os.environ.setdefault("MUJOCO_GL", "egl")

    import imageio.v2 as imageio
    import mujoco as mj

    motion = load_motion(motion_path)
    model_path = resolve_from_repo(motion["robot_model"])
    model = mj.MjModel.from_xml_path(str(model_path))
    data = mj.MjData(model)
    joint_names = motion["joint_names"]
    positions = motion["joint_positions"]

    joint_qpos_adr = {}
    for name in joint_names:
        joint_id = mj.mj_name2id(model, mj.mjtObj.mjOBJ_JOINT, name)
        if joint_id < 0:
            raise RuntimeError(f"Preview model is missing joint {name!r}")
        joint_qpos_adr[name] = int(model.jnt_qposadr[joint_id])

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    renderer = mj.Renderer(model, width=width, height=height)
    camera = mj.MjvCamera()
    camera.distance = 1.25
    camera.azimuth = 145
    camera.elevation = -15
    camera.lookat[:] = np.array([0.02, 0.0, 0.35])

    fps = max(float(motion["fps"]), 1.0)
    with imageio.get_writer(output_path, fps=fps) as writer:
        for row in positions:
            for name, value in zip(joint_names, row):
                data.qpos[joint_qpos_adr[name]] = float(value)
            mj.mj_forward(model, data)
            renderer.update_scene(data, camera=camera)
            writer.append_data(renderer.render())
    renderer.close()
    return output_path
