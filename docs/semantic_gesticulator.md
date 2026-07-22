# Semantic-Gesticulator Story Pipeline

This repository can use Semantic-Gesticulator as an alternate motion source:

```text
text/story -> WAV -> Semantic-Gesticulator -> BVH -> MindBot GMR retarget -> Isaac replay
```

GVHMR is not used in this path. Semantic-Gesticulator already outputs a BVH skeleton motion, and this project converts that BVH into the same `human_frames` contract used by the GVHMR path.

## Setup

Clone and install the optional Semantic-Gesticulator runtime:

```bash
./scripts/setup_semantic_gesticulator.sh
```

This creates:

```text
third_party/Semantic-Gesticulator-Official/
.venv-semantic/
```

The upstream models are license-gated or hosted separately, so the setup script does not download them. Put the official assets in:

```text
third_party/Semantic-Gesticulator-Official/SG_code/pretrained_models/
  rqvae.pt
  gpt_0.pt
  gpt_1.pt
  gpt_2.pt
  gpt_3.pt

third_party/Semantic-Gesticulator-Official/SG_code/retrieval_model/
  model-00001-of-00004.safetensors
  model-00002-of-00004.safetensors
  model-00003-of-00004.safetensors
  model-00004-of-00004.safetensors
  ...

third_party/Semantic-Gesticulator-Official/SG_code/Data/SG_processed/
  audio_feature_scaler.sav
  motion_data_template.pkl
  config.json
  body_scaler.sav
```

The semantic insertion path also expects:

```text
third_party/Semantic-Gesticulator-Official/SG_code/SG_pipeline/all_mocap_extracted_new.npz
```

## Run From Text

```bash
./scripts/run_semantic_story_pipeline.sh \
  --text "Hello everyone. Let me explain how this robot works." \
  --output-dir outputs/story \
  --replay
```

If no `--audio` is passed, the script creates `outputs/story/story.wav` with `espeak-ng` or `espeak`. For Chinese or other voices, install the matching local TTS voice and pass:

```bash
./scripts/run_semantic_story_pipeline.sh \
  --text-file story.txt \
  --tts-voice zh \
  --output-dir outputs/story_cn
```

If local text-to-speech is not installed, create a WAV externally and pass:

```bash
./scripts/run_semantic_story_pipeline.sh \
  --audio path/to/story.wav \
  --output-dir outputs/story_audio
```

## Run From Existing BVH

If Semantic-Gesticulator has already generated a BVH:

```bash
./scripts/retarget_bvh_to_mindbot.sh \
  --bvh path/to/story_semantic_results.bvh \
  --output-dir outputs/story_bvh
```

This writes:

```text
outputs/story_bvh/mindbot_motion.npz
outputs/story_bvh/joint_trajectory.csv
outputs/story_bvh/retarget_report.json
outputs/story_bvh/retarget_preview.mp4
```

## Coordinate Tuning

The default BVH axis mode is:

```text
--coordinate-mode y_up_z_forward
```

If the robot faces backward or mirrors the gesture, rerun only the BVH retarget stage with one of:

```text
y_up_z_forward
y_up_minus_z_forward
z_up_y_forward
z_up_minus_y_forward
```

Semantic-Gesticulator/ZeroEGGS-style BVH usually uses centimeter-scale offsets, so the default scale is:

```text
--scale 0.01
```

Use `--scale 1.0` only for BVH files already in meters.

## Waist Behavior

The default is:

```text
--waist-mode torso_heading
```

This estimates waist yaw from shoulder and hip geometry, so the robot turns its waist when the generated speaker turns. Use:

```text
--waist-mode locked
```

for arm-only debugging.
