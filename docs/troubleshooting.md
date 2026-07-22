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

The default `--waist-mode torso_heading` estimates waist yaw from SMPL-X shoulder and hip geometry, then smooths it before robot-limit filtering. This follows real body turns without using the noisier per-frame global spine quaternion.

Use `--waist-mode locked` for arm-only debugging. Use `--waist-mode spine_yaw` only to inspect the raw spine orientation path; single-camera GVHMR global yaw can jump when the person turns, the camera moves, or depth is ambiguous.

## Isaac Launcher Fails

Confirm:

```bash
./.venv-tools/bin/python scripts/inspect_official_environment.py
./scripts/replay_in_isaac.sh --motion outputs/test/mindbot_motion.npz --headless
```

If the official launcher cannot find Isaac Lab, fix the official environment first. This project intentionally does not modify that environment.
