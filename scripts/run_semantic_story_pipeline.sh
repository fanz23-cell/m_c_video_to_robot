#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

text=""
text_file=""
audio=""
bvh=""
output_dir=""
tts_voice=""
semantic=true
replay=false
preview=true
robot="mindbot_dual_arm"
target_fps="30"
scale="0.01"
coordinate_mode="y_up_z_forward"
waist_mode="torso_heading"
sg_root="${SEMANTIC_GESTICULATOR_ROOT:-${REPO_ROOT}/third_party/Semantic-Gesticulator-Official/SG_code}"
sg_python="${SEMANTIC_GESTICULATOR_PYTHON:-${REPO_ROOT}/.venv-semantic/bin/python}"
processed_dataset_dir=""
rqvae_path=""
model_path_0=""
model_path_1=""
model_path_2=""
model_path_3=""
sg_codebook=""
retrieval_model_path=""
init_body_pose_code="128"
init_hands_pose_code="258"
cuda_visible_devices="${CUDA_VISIBLE_DEVICES:-0}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --text|--story)
      text="$2"
      shift 2
      ;;
    --text-file|--story-file)
      text_file="$2"
      shift 2
      ;;
    --audio)
      audio="$2"
      shift 2
      ;;
    --bvh)
      bvh="$2"
      shift 2
      ;;
    --output-dir)
      output_dir="$2"
      shift 2
      ;;
    --tts-voice)
      tts_voice="$2"
      shift 2
      ;;
    --sg-root)
      sg_root="$2"
      shift 2
      ;;
    --sg-python)
      sg_python="$2"
      shift 2
      ;;
    --processed-dataset-dir)
      processed_dataset_dir="$2"
      shift 2
      ;;
    --rqvae-path)
      rqvae_path="$2"
      shift 2
      ;;
    --model-path-0)
      model_path_0="$2"
      shift 2
      ;;
    --model-path-1)
      model_path_1="$2"
      shift 2
      ;;
    --model-path-2)
      model_path_2="$2"
      shift 2
      ;;
    --model-path-3)
      model_path_3="$2"
      shift 2
      ;;
    --sg-codebook)
      sg_codebook="$2"
      shift 2
      ;;
    --retrieval-model-path)
      retrieval_model_path="$2"
      shift 2
      ;;
    --init-body-pose-code)
      init_body_pose_code="$2"
      shift 2
      ;;
    --init-hands-pose-code)
      init_hands_pose_code="$2"
      shift 2
      ;;
    --cuda-visible-devices)
      cuda_visible_devices="$2"
      shift 2
      ;;
    --robot)
      robot="$2"
      shift 2
      ;;
    --target-fps)
      target_fps="$2"
      shift 2
      ;;
    --scale)
      scale="$2"
      shift 2
      ;;
    --coordinate-mode)
      coordinate_mode="$2"
      shift 2
      ;;
    --waist-mode)
      waist_mode="$2"
      shift 2
      ;;
    --semantic)
      semantic=true
      shift
      ;;
    --no-semantic)
      semantic=false
      shift
      ;;
    --replay)
      replay=true
      shift
      ;;
    --no-preview)
      preview=false
      shift
      ;;
    *)
      echo "[ERROR] Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ "${robot}" != "mindbot_dual_arm" ]; then
  echo "[ERROR] Only --robot mindbot_dual_arm is supported in this stage." >&2
  exit 2
fi

if [ -z "${output_dir}" ]; then
  output_dir="outputs/semantic_story"
fi
mkdir -p "${output_dir}"

if [ -z "${bvh}" ]; then
  if [ -z "${audio}" ]; then
    audio="${output_dir}/story.wav"
    tools_python="${REPO_ROOT}/.venv-tools/bin/python"
    if [ ! -x "${tools_python}" ]; then
      tools_python="python3"
    fi
    tts_cmd=("${tools_python}" "-m" "m_c_video_to_robot.story_audio" "--output" "${audio}")
    if [ -n "${text}" ]; then
      tts_cmd+=("--text" "${text}")
    elif [ -n "${text_file}" ]; then
      tts_cmd+=("--text-file" "${text_file}")
    else
      echo "[ERROR] Provide --text, --text-file, --audio, or --bvh." >&2
      exit 2
    fi
    if [ -n "${tts_voice}" ]; then
      tts_cmd+=("--voice" "${tts_voice}")
    fi
    PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}" "${tts_cmd[@]}"
  fi

  if [ ! -f "${audio}" ]; then
    echo "[ERROR] Audio file not found: ${audio}" >&2
    exit 1
  fi
  if [ ! -d "${sg_root}" ]; then
    echo "[ERROR] Semantic-Gesticulator SG_code not found: ${sg_root}" >&2
    echo "        Run ./scripts/setup_semantic_gesticulator.sh, or pass --sg-root /path/to/Semantic-Gesticulator-Official/SG_code" >&2
    exit 1
  fi
  if [ ! -x "${sg_python}" ]; then
    echo "[ERROR] Semantic-Gesticulator Python not found: ${sg_python}" >&2
    echo "        Run ./scripts/setup_semantic_gesticulator.sh, or pass --sg-python /path/to/python" >&2
    exit 1
  fi

  processed_dataset_dir="${processed_dataset_dir:-${sg_root}/Data/SG_processed}"
  rqvae_path="${rqvae_path:-${sg_root}/pretrained_models/rqvae.pt}"
  model_path_0="${model_path_0:-${sg_root}/pretrained_models/gpt_0.pt}"
  model_path_1="${model_path_1:-${sg_root}/pretrained_models/gpt_1.pt}"
  model_path_2="${model_path_2:-${sg_root}/pretrained_models/gpt_2.pt}"
  model_path_3="${model_path_3:-${sg_root}/pretrained_models/gpt_3.pt}"
  sg_codebook="${sg_codebook:-${sg_root}/SG_pipeline/all_mocap_extracted_new.npz}"
  retrieval_model_path="${retrieval_model_path:-${sg_root}/retrieval_model}"

  required_files=("${processed_dataset_dir}/audio_feature_scaler.sav" "${processed_dataset_dir}/motion_data_template.pkl" "${rqvae_path}" "${model_path_0}" "${model_path_1}" "${model_path_2}" "${model_path_3}")
  if [ "${semantic}" = true ]; then
    required_files+=("${sg_codebook}")
    if [ ! -d "${retrieval_model_path}" ]; then
      echo "[ERROR] Missing retrieval model directory: ${retrieval_model_path}" >&2
      exit 1
    fi
  fi
  for required in "${required_files[@]}"; do
    if [ ! -f "${required}" ]; then
      echo "[ERROR] Missing Semantic-Gesticulator asset: ${required}" >&2
      exit 1
    fi
  done

  sg_save_dir="${output_dir}/semantic_gesticulator"
  mkdir -p "${sg_save_dir}"
  audio_name="$(basename "${audio}")"
  audio_name="${audio_name%.*}"
  if [ "${semantic}" = true ]; then
    generator="${sg_root}/generate_semantic_gestures.py"
    generated_suffix="semantic_results"
  else
    generator="${sg_root}/generate_gestures.py"
    generated_suffix="original_motion"
  fi

  if [ ! -f "${generator}" ]; then
    echo "[ERROR] Semantic-Gesticulator generator not found: ${generator}" >&2
    exit 1
  fi

  sg_cmd=(
    "${sg_python}" "-m" "torch.distributed.launch"
    "--nproc_per_node=1"
    "--master_port=29502"
    "${generator}"
    "--audio_path" "${audio}"
    "--save_dir" "${sg_save_dir}"
    "--rqvae_path" "${rqvae_path}"
    "--model_path_0" "${model_path_0}"
    "--model_path_1" "${model_path_1}"
    "--model_path_2" "${model_path_2}"
    "--model_path_3" "${model_path_3}"
    "--init_body_pose_code" "${init_body_pose_code}"
    "--init_hands_pose_code" "${init_hands_pose_code}"
    "--processed_dataset_dir" "${processed_dataset_dir}"
  )
  if [ "${semantic}" = true ]; then
    sg_cmd+=("--sg_codebook" "${sg_codebook}" "--retrieval_model_path" "${retrieval_model_path}")
  fi

  (cd "${sg_root}" && CUDA_VISIBLE_DEVICES="${cuda_visible_devices}" "${sg_cmd[@]}")
  bvh="${sg_save_dir}/${audio_name}/${audio_name}_${generated_suffix}.bvh"
fi

if [ ! -f "${bvh}" ]; then
  echo "[ERROR] Generated BVH not found: ${bvh}" >&2
  exit 1
fi

retarget_args=(
  "--bvh" "${bvh}"
  "--output-dir" "${output_dir}"
  "--robot" "${robot}"
  "--target-fps" "${target_fps}"
  "--scale" "${scale}"
  "--coordinate-mode" "${coordinate_mode}"
  "--waist-mode" "${waist_mode}"
)
if [ "${preview}" = false ]; then
  retarget_args+=("--no-preview")
fi

"${REPO_ROOT}/scripts/retarget_bvh_to_mindbot.sh" "${retarget_args[@]}"

if [ "${replay}" = true ]; then
  "${REPO_ROOT}/scripts/replay_in_isaac.sh" --motion "${output_dir}/mindbot_motion.npz"
fi
