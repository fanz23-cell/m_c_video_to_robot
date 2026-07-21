# GMR Adapter

Official repository:

```text
https://github.com/YanjieZe/GMR.git
```

Current submodule commit:

```text
bb1bbe40774794fceb2a7c579a3464a28e68c844
```

The project does not edit GMR `params.py`. It registers MindBot dynamically:

```python
gmr_params.ROBOT_XML_DICT["mindbot_dual_arm"] = robot_xml
gmr_params.IK_CONFIG_DICT["smplx"]["mindbot_dual_arm"] = ik_config
```

The generated robot model is created from the official Isaac URDF:

```bash
./.venv-gmr/bin/python scripts/build_mindbot_gmr_model.py
```

Output:

```text
build/mindbot_gmr/mindbot.urdf
build/mindbot_gmr/mindbot.xml
```

The build script keeps base, waist, left arm, right arm, and TCP links. It removes the RealSense branch from the GMR IK model and does not change waist or arm origins, axes, limits, or link transforms.

The first mapping uses:

```text
pelvis, spine3, left_shoulder, left_elbow, left_wrist,
right_shoulder, right_elbow, right_wrist
```

to target:

```text
waist_link, left_arm_link_1, left_arm_link_3, left_arm_link_6,
right_arm_link_1, right_arm_link_3, right_arm_link_6
```

These links were selected after reading the official URDF chain and are documented in `docs/official_environment_inventory.md`. The generated MuJoCo XML folds the fixed base and fixed TCP bodies, so the low-weight pelvis/root offset task uses the MuJoCo `world` body and wrist/end-effector tasks use arm link 6; the Isaac replay still uses the official environment and named joints.
