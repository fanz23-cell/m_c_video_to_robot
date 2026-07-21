# Isaac Replay

Replay command:

```bash
./scripts/replay_in_isaac.sh \
  --motion outputs/test/mindbot_motion.npz
```

The wrapper first validates the motion with `.venv-isaac`, then calls:

```text
${MINDBOT_ISAAC_ROOT}/mindbot_isaaclab.sh
```

The actual Isaac script is:

```text
src/m_c_video_to_robot/isaac_replay.py
```

It loads `Mindbot-DualArmWaist-Realsense-Play-v0`, resolves articulation joints by name, interpolates by timestamp, and sends named position targets through the official `make_joint_position_action` helper.

Supported replay options:

```bash
./scripts/replay_in_isaac.sh \
  --motion outputs/test/mindbot_motion.npz \
  --loop \
  --speed 0.5 \
  --record
```

The official launcher must be able to start Isaac Lab from its own environment or from an already-active venv. This repository does not install GVHMR or GMR dependencies into the official Isaac environment.
