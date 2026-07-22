# Troubleshooting

## Missing GVHMR Assets

Run:

```bash
./.venv-tools/bin/python scripts/check_gvhmr_assets.py
```

The output lists each missing filename, relative directory, official download source, and next command.

## Left And Right Arms Are Mirrored

Check:

```text
configs/smplx_to_mindbot.json
docs/official_environment_inventory.md
```

Tune the task quaternion offsets and weights for the affected shoulder, elbow, or wrist target. Re-run only the retarget stage.

## Elbows Bend The Wrong Way

Reduce wrist orientation weight first, then increase elbow position weight. For single-frame debugging, use `--start-frame N --end-frame N+1` with `retarget_to_mindbot.sh`.

## Waist Snaps Near 180 Degrees

The retargeter locks `waist_joint` at `0.0` rad by default. Single-camera GVHMR global yaw can jump when the person turns, the camera moves, or depth is ambiguous, and a fixed-base robot waist makes those jumps very visible.

Use `--waist-mode spine_yaw` only for videos where deliberate body turning matters. If that mode snaps, inspect `raw_joint_positions` in `mindbot_motion.npz` and lower the smoothing window in `configs/filters.yaml`.

## Isaac Launcher Fails

Confirm:

```bash
./.venv-tools/bin/python scripts/inspect_official_environment.py
./scripts/replay_in_isaac.sh --motion outputs/test/mindbot_motion.npz --headless
```

If the official launcher cannot find Isaac Lab, fix the official environment first. This project intentionally does not modify that environment.
