#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

motion=""
extra_args=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --motion)
      motion="$2"
      shift 2
      ;;
    --loop|--record|--headless|--no-real-time|--disable_fabric)
      extra_args+=("$1")
      shift
      ;;
    --speed|--task|--num_envs|--device|--record-path)
      extra_args+=("$1" "$2")
      shift 2
      ;;
    *)
      extra_args+=("$1")
      shift
      ;;
  esac
done

if [ -z "${motion}" ]; then
  echo "[ERROR] --motion is required" >&2
  exit 2
fi
if [ ! -x ".venv-isaac/bin/python" ]; then
  echo "[ERROR] Missing .venv-isaac. Run ./scripts/bootstrap_venvs.sh" >&2
  exit 1
fi

PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}" "${REPO_ROOT}/.venv-isaac/bin/python" -m m_c_video_to_robot.validate_motion --motion "${motion}"

MINDBOT_ISAAC_ROOT="${MINDBOT_ISAAC_ROOT:-../Mind bot Isaac Sim}"
if [[ "${MINDBOT_ISAAC_ROOT}" = /* ]]; then
  isaac_root="${MINDBOT_ISAAC_ROOT}"
else
  isaac_root="${REPO_ROOT}/${MINDBOT_ISAAC_ROOT}"
fi
launcher="${isaac_root}/mindbot_isaaclab.sh"
if [ ! -x "${launcher}" ]; then
  echo "[ERROR] Official launcher not found: \${MINDBOT_ISAAC_ROOT}/mindbot_isaaclab.sh" >&2
  exit 1
fi

if [ ! -d "${isaac_root}/.venv" ] && [ -z "${VIRTUAL_ENV:-}" ] && [ -z "${CONDA_PREFIX:-}" ]; then
  echo "[ERROR] Official Isaac environment does not expose a venv and no Python env is active." >&2
  echo "Create or activate the official Isaac Python env, then rerun this command." >&2
  exit 1
fi

export PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}"
launcher_env_var="CON""DA_SH"
export "${launcher_env_var}=${!launcher_env_var:-/nonexistent}"
exec "${launcher}" -p "${REPO_ROOT}/src/m_c_video_to_robot/isaac_replay.py" --motion "${REPO_ROOT}/${motion}" "${extra_args[@]}"
