#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/m_c_video_to_robot_matplotlib}"
export YOLO_CONFIG_DIR="${YOLO_CONFIG_DIR:-/tmp/m_c_video_to_robot_ultralytics}"
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD="${TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD:-1}"

video=""
static_camera=0
use_dpvo=0
f_mm=""

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
    --use-dpvo)
      use_dpvo=1
      shift
      ;;
    --f-mm)
      f_mm="$2"
      shift 2
      ;;
    *)
      echo "[ERROR] Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ -z "${video}" ]; then
  echo "[ERROR] --video is required" >&2
  exit 2
fi
if [ ! -f "${video}" ]; then
  echo "[ERROR] Video not found: ${video}" >&2
  exit 1
fi
if [ ! -x ".venv-gvhmr/bin/python" ]; then
  echo "[ERROR] Missing .venv-gvhmr. Run ./scripts/bootstrap_venvs.sh" >&2
  exit 1
fi

stem="$(basename "${video}")"
stem="${stem%.*}"
output_root="outputs/${stem}/gvhmr"
mkdir -p "${output_root}"

args=(tools/demo/demo.py "--video=${REPO_ROOT}/${video}" "--output_root=${REPO_ROOT}/${output_root}" "--no_render")
if [ "${static_camera}" -eq 1 ]; then
  args+=("--static_cam")
fi
if [ "${use_dpvo}" -eq 1 ]; then
  args+=("--use_dpvo")
fi
if [ -n "${f_mm}" ]; then
  args+=("--f_mm=${f_mm}")
fi

(
  cd "${REPO_ROOT}/third_party/GVHMR"
  "${REPO_ROOT}/.venv-gvhmr/bin/python" "${args[@]}"
)

echo "${output_root}/${stem}/hmr4d_results.pt"
