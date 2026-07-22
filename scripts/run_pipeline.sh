#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

video=""
static_camera=0
record=0
robot="mindbot_dual_arm"
waist_mode="locked"
replay_args=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --video)
      video="$2"
      shift 2
      ;;
    --static-camera)
      static_camera=1
      shift
      ;;
    --robot)
      robot="$2"
      shift 2
      ;;
    --waist-mode)
      waist_mode="$2"
      shift 2
      ;;
    --record)
      record=1
      shift
      ;;
    --loop|--headless|--no-real-time)
      replay_args+=("$1")
      shift
      ;;
    --speed|--task|--num_envs|--device)
      replay_args+=("$1" "$2")
      shift 2
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
if [ -z "${video}" ]; then
  echo "[ERROR] --video is required" >&2
  exit 2
fi

./scripts/check_dependencies.sh
./.venv-tools/bin/python scripts/check_gvhmr_assets.py

extract_args=(--video "${video}")
if [ "${static_camera}" -eq 1 ]; then
  extract_args+=(--static-camera)
fi
gvhmr_output="$(./scripts/extract_human_motion.sh "${extract_args[@]}" | tail -n 1)"

stem="$(basename "${video}")"
stem="${stem%.*}"
./scripts/retarget_to_mindbot.sh --gvhmr-output "${gvhmr_output}" --output-dir "outputs/${stem}" --source-video "${video}" --robot "${robot}" --waist-mode "${waist_mode}"

motion="outputs/${stem}/mindbot_motion.npz"
if [ "${record}" -eq 1 ]; then
  replay_args+=(--record)
fi
./scripts/replay_in_isaac.sh --motion "${motion}" "${replay_args[@]}"
