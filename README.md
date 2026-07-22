# m_c_video_to_robot

Input a normal MP4 of a person, recover 3D human motion with official GVHMR, retarget upper-body motion to the MindBot dual-arm waist robot with official GMR, then replay the named joint trajectory in the existing MindBot Isaac Lab environment.

This stage is simulation-only:

- no real robot connection
- no reinforcement learning
- no wheel/base motion
- no edits to the official Isaac environment
- Python environments are repo-local `venv` directories

## Quick Start

```bash
git clone --recurse-submodules https://github.com/<USERNAME>/m_c_video_to_robot.git
cd m_c_video_to_robot

cp .env.example .env

./scripts/bootstrap_venvs.sh
./scripts/check_dependencies.sh
./.venv-tools/bin/python scripts/check_gvhmr_assets.py

./scripts/run_pipeline.sh \
  --video data/input_videos/test.mp4 \
  --static-camera \
  --record
```

If you clone without submodules:

```bash
git submodule update --init --recursive
```

## Isaac Path

The default official environment path is:

```bash
MINDBOT_ISAAC_ROOT="../Mind bot Isaac Sim"
```

Change `.env` if your official Isaac project is somewhere else:

```bash
cp .env.example .env
```

All repository code resolves this path from the repository root. Generated motion metadata stores repository-relative paths only.

## Environments

The project uses four separate venvs:

```text
.venv-tools  project checks, docs inventory, tests
.venv-gvhmr  GVHMR only
.venv-gmr    GMR, MuJoCo, Mink, retargeting
.venv-isaac  motion validation and Isaac replay wrapper
```

Conda-style environments are intentionally avoided so GVHMR, GMR, Isaac wrapper code, and project tooling do not leak dependencies into each other.

## Put Files Here

- Input videos: `data/input_videos/`
- GVHMR checkpoints: `third_party/GVHMR/inputs/checkpoints/`
- GMR SMPL-X body models: `third_party/GMR/assets/body_models/smplx/`
- Generated GMR robot model: `build/mindbot_gmr/`
- Outputs: `outputs/<video_name>/`

Do not commit SMPL/SMPL-X models, checkpoints, videos, generated motions, recordings, or `.env`.

## Run In Stages

GVHMR:

```bash
./scripts/extract_human_motion.sh \
  --video data/input_videos/test.mp4 \
  --static-camera
```

GMR to MindBot:

```bash
./scripts/retarget_to_mindbot.sh \
  --gvhmr-output outputs/test/gvhmr/test/hmr4d_results.pt \
  --output-dir outputs/test \
  --source-video data/input_videos/test.mp4
```

Isaac replay:

```bash
./scripts/replay_in_isaac.sh \
  --motion outputs/test/mindbot_motion.npz
```

Slow loop with recording:

```bash
./scripts/replay_in_isaac.sh \
  --motion outputs/test/mindbot_motion.npz \
  --loop \
  --speed 0.5 \
  --record
```

## Motion Format

`outputs/<video_name>/mindbot_motion.npz` contains:

- `joint_names`
- `joint_positions`
- `raw_joint_positions`
- `timestamps`
- `fps`
- `source_video`
- `source_gvhmr_file`
- `robot_model`
- `gmr_commit`
- `gvhmr_commit`

The joint order is explicit:

```text
waist_joint
left_arm_joint_1 ... left_arm_joint_6
right_arm_joint_1 ... right_arm_joint_6
```

Wheel/base commands are not emitted. The waist is locked at `0.0` rad by default because monocular GVHMR global yaw can jump on fixed-base robots. Use `--waist-mode spine_yaw` only when the source video clearly needs body turning.

## Mapping And Smoothing

- Human-to-robot tasks: `configs/smplx_to_mindbot.json`
- Robot joint names and limits: `configs/mindbot_robot.yaml`
- Filtering, transitions, velocity margin: `configs/filters.yaml`

If left/right arms are visually mirrored or elbows bend the wrong way, first inspect `docs/official_environment_inventory.md`, then tune the affected task weights and quaternion offsets in `configs/smplx_to_mindbot.json`.

## Official Environment

Run:

```bash
./.venv-tools/bin/python scripts/inspect_official_environment.py
```

This regenerates `docs/official_environment_inventory.md` and confirms the official URDF, extension, launcher, registered tasks, joint names, limits, and action mode.

## Checks

```bash
./scripts/check_no_absolute_paths.sh
./scripts/run_tests.sh
git status --short
git diff --check
```

The local absolute-path check is implemented without embedding this machine's expanded workspace path into tracked files.

## GitHub Publish

```bash
./scripts/publish_github.sh
```

If GitHub CLI is not logged in, run:

```bash
gh auth login
```

The publish script creates `m_c_video_to_robot` as a private repository by default and pushes `main`.
