# Architecture

The pipeline is intentionally split by dependency boundary:

1. `extract_human_motion.sh` runs official GVHMR in `.venv-gvhmr` and produces `hmr4d_results.pt`.
2. `retarget_to_mindbot.sh` runs official GMR in `.venv-gmr`, dynamically registers `mindbot_dual_arm`, and writes a named joint trajectory.
3. `replay_in_isaac.sh` validates the motion in `.venv-isaac`, then launches the official Isaac Lab environment with this repository's replay script.

The official Isaac environment is read-only from this project. We use its existing URDF, launcher, registered tasks, and `mindbot_isaac_sim.interfaces.make_joint_position_action` helper.

## Data Contracts

GVHMR output:

```text
outputs/<video>/gvhmr/<video>/hmr4d_results.pt
```

MindBot motion output:

```text
outputs/<video>/mindbot_motion.npz
outputs/<video>/joint_trajectory.csv
outputs/<video>/retarget_report.json
outputs/<video>/retarget_preview.mp4
```

`mindbot_motion.npz` never relies on MuJoCo `qpos` order. It stores explicit `joint_names`, and Isaac replay uses those names to build actions.

## Control Scope

The first stage controls two six-DOF arms and keeps the waist yaw locked by default. `--waist-mode spine_yaw` can be used for deliberate body-turning videos, but RealSense pitch, wheels, and base motion are held by the official environment defaults.
