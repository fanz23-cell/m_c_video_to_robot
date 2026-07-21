# Test Log

This file records what was actually run. Do not mark a heavy stage as successful unless its command completed on this machine.

## Static Project Checks

Command:

```bash
PYTHONPATH=src python3 scripts/inspect_official_environment.py
```

Result: completed and generated `docs/official_environment_inventory.md`.

Command:

```bash
./scripts/bootstrap_venvs.sh
```

Result: `.venv-tools`, `.venv-gvhmr`, `.venv-gmr`, and `.venv-isaac` were created. Tools, GMR, and Isaac wrapper dependencies installed. GVHMR dependency installation was skipped because this machine's `python3` is Python 3.12 while the official GVHMR requirements pin a Python 3.10 PyTorch3D wheel.

Fix:

```bash
PYTHON_GVHMR=python3.10 ./scripts/bootstrap_venvs.sh
```

Command:

```bash
./.venv-gmr/bin/python scripts/build_mindbot_gmr_model.py --force
```

Result: completed and generated `build/mindbot_gmr/mindbot.xml`.

Command:

```bash
git submodule update --init --recursive
```

Result: completed. GVHMR's nested DPVO submodule and its nested dependencies were initialized.

Command:

```bash
./scripts/run_tests.sh
```

Result: passed, `2 passed`.

Command:

```bash
./.venv-isaac/bin/python -m m_c_video_to_robot.validate_motion --motion outputs/smoke/mindbot_motion.npz
```

Result: passed on a generated zero-position smoke motion with 13 named joints.

Command:

```bash
./.venv-gmr/bin/python -c "from m_c_video_to_robot.preview import create_mujoco_preview; create_mujoco_preview('outputs/smoke/mindbot_motion.npz', 'outputs/smoke/retarget_preview.mp4')"
```

Result: passed after setting the preview renderer to use EGL by default.

Command:

```bash
custom single-frame GMR smoke using a hand-built SMPL-X key-body frame
```

Result: passed. Dynamic `mindbot_dual_arm` registration loaded `build/mindbot_gmr/mindbot.xml`, solved one frame, and produced finite values for all 13 controlled joints.

Command:

```bash
./.venv-tools/bin/python scripts/check_gvhmr_assets.py
```

Result: failed as expected because licensed SMPL/SMPL-X files and GVHMR checkpoints are not present.

Command:

```bash
./scripts/check_dependencies.sh
```

Result: failed because `.venv-gvhmr` currently uses Python 3.12. Tools, GMR, and Isaac wrapper import checks passed.

## Heavy Pipeline Tests

The following require venv dependency installation and licensed model assets:

1. GVHMR official example video to `hmr4d_results.pt`
2. GVHMR result to GMR official Unitree G1
3. Single-frame MindBot retarget
4. Three-to-five-second MuJoCo preview
5. Full motion preview
6. Isaac Sim replay
7. User MP4 replay

Record each command, log path, result files, failure reason, and fix here after running.
