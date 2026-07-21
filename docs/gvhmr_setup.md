# GVHMR Setup

Official repository:

```text
https://github.com/zju3dv/GVHMR.git
```

Current submodule commit:

```text
6ec3ca39336c50492c0fae65fba2fb831fc7d866
```

Run:

```bash
./.venv-tools/bin/python scripts/check_gvhmr_assets.py
```

Required GVHMR files live under:

```text
third_party/GVHMR/inputs/checkpoints/
```

SMPL and SMPL-X files must be downloaded from their official license-gated sites. GVHMR checkpoints are listed in `third_party/GVHMR/docs/INSTALL.md`.

Stage command:

```bash
./scripts/extract_human_motion.sh \
  --video data/input_videos/test.mp4 \
  --static-camera
```

Output:

```text
outputs/test/gvhmr/test/hmr4d_results.pt
```
