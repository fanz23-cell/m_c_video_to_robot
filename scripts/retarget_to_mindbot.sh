#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

gvhmr_output=""
output_dir=""
source_video=""
extra_args=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --gvhmr-output)
      gvhmr_output="$2"
      shift 2
      ;;
    --output-dir)
      output_dir="$2"
      shift 2
      ;;
    --source-video)
      source_video="$2"
      shift 2
      ;;
    --robot)
      extra_args+=("--robot" "$2")
      shift 2
      ;;
    --start-frame|--end-frame|--target-fps|--smplx-body-models)
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

if [ -z "${gvhmr_output}" ]; then
  echo "[ERROR] --gvhmr-output is required" >&2
  exit 2
fi
if [ ! -f "${gvhmr_output}" ]; then
  echo "[ERROR] GVHMR output not found: ${gvhmr_output}" >&2
  exit 1
fi
if [ ! -x ".venv-gmr/bin/python" ]; then
  echo "[ERROR] Missing .venv-gmr. Run ./scripts/bootstrap_venvs.sh" >&2
  exit 1
fi
if [ -z "${output_dir}" ]; then
  video_name="$(basename "$(dirname "${gvhmr_output}")")"
  output_dir="outputs/${video_name}"
fi

cmd=("${REPO_ROOT}/.venv-gmr/bin/python" "-m" "m_c_video_to_robot.retarget" "--gvhmr-output" "${gvhmr_output}" "--output-dir" "${output_dir}")
if [ -n "${source_video}" ]; then
  cmd+=("--source-video" "${source_video}")
fi
cmd+=("${extra_args[@]}")

PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}" "${cmd[@]}"
