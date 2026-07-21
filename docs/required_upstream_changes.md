# Required Upstream Changes

No upstream source changes are required at this stage.

GMR is extended through `src/m_c_video_to_robot/gmr_registration.py`, which dynamically inserts `mindbot_dual_arm` into GMR's robot and IK dictionaries at runtime.

If a future change must patch GMR, store the patch in:

```text
patches/GMR/
```

and apply it with:

```bash
./scripts/apply_gmr_patches.sh
```

Do not leave unrecorded modifications inside `third_party/GMR`.
