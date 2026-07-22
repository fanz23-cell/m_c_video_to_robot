#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

bvh=""
output_dir=""
extra_args=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --bvh)
      bvh="$2"
      shift 2
      ;;
    --output-dir)
      output_dir="$2"
      shift 2
      ;;
    --robot)
      extra_args+=("--robot" "$2")
      shift 2
      ;;
    --start-frame|--end-frame|--target-fps|--scale|--coordinate-mode|--waist-mode)
      extra_args+=("$1" "$2")
      shift 2
      ;;
    --rebuild-model|--verbose|--no-preview)
      extra_args+=("$1")
      shift
      ;;
    *)
      echo "[ERROR] Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ -z "${bvh}" ]; then
  echo "[ERROR] --bvh is required" >&2
  exit 2
fi
if [ ! -f "${bvh}" ]; then
  echo "[ERROR] BVH file not found: ${bvh}" >&2
  exit 1
fi
if [ ! -x ".venv-gmr/bin/python" ]; then
  echo "[ERROR] Missing .venv-gmr. Run ./scripts/bootstrap_venvs.sh" >&2
  exit 1
fi
if [ -z "${output_dir}" ]; then
  stem="$(basename "${bvh}")"
  stem="${stem%.*}"
  output_dir="outputs/${stem}"
fi

cmd=("${REPO_ROOT}/.venv-gmr/bin/python" "-m" "m_c_video_to_robot.bvh_to_mindbot" "--bvh" "${bvh}" "--output-dir" "${output_dir}")
cmd+=("${extra_args[@]}")

PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}" "${cmd[@]}"
