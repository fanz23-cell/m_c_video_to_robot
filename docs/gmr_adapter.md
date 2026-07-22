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

The MindBot mapping uses:

```text
spine3, left_shoulder, left_elbow, left_wrist,
right_shoulder, right_elbow, right_wrist
```

to target:

```text
waist_link,
left_arm_link_1, left_arm_link_4, left_arm_tcp,
right_arm_link_1, right_arm_link_4, right_arm_tcp
```

These links were selected after reading the official URDF chain and are documented in `docs/official_environment_inventory.md`. GVHMR/SMPL-X frames are first converted into the fixed-base MindBot arm workspace: human lateral X becomes robot lateral Y, shoulders are anchored to the robot shoulder frames, and upper-arm/forearm targets are scaled to the robot segment lengths. The generated MuJoCo XML normally folds fixed TCP links, so the build step adds massless `left_arm_tcp` and `right_arm_tcp` task frames back under arm link 6.

The GMR IK config uses position-dominant constraints. Shoulder targets are weak anchors, while elbow and TCP targets carry the main costs. Wrist orientation costs are intentionally zero in this stage because a monocular human wrist orientation is noisy and can overconstrain the MindBot 6-DoF arms.
