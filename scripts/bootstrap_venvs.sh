#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 not found. Install it with: sudo apt install python3 python3-venv" >&2
  exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "[ERROR] python3 venv support is missing. Install it with: sudo apt install python3-venv" >&2
  exit 1
fi

create_venv() {
  local name="$1"
  local python_bin="$2"
  if ! command -v "${python_bin}" >/dev/null 2>&1; then
    echo "[ERROR] Python interpreter not found for ${name}: ${python_bin}" >&2
    return 1
  fi
  local requested_version
  requested_version="$("${python_bin}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if [ ! -x "${name}/bin/python" ]; then
    echo "[INFO] Creating ${name}"
    "${python_bin}" -m venv "${name}"
  else
    local existing_version
    existing_version="$("${REPO_ROOT}/${name}/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if [ "${existing_version}" != "${requested_version}" ]; then
      echo "[INFO] Recreating ${name}: existing Python ${existing_version}, requested ${requested_version}"
      "${python_bin}" -m venv --clear "${name}"
    fi
  fi
  "${REPO_ROOT}/${name}/bin/python" -m pip install --upgrade pip setuptools wheel
}

PYTHON_TOOLS="${PYTHON_TOOLS:-python3}"
PYTHON_GVHMR="${PYTHON_GVHMR:-python3}"
PYTHON_GMR="${PYTHON_GMR:-python3}"
PYTHON_ISAAC="${PYTHON_ISAAC:-python3}"

create_venv .venv-tools "${PYTHON_TOOLS}"
create_venv .venv-gvhmr "${PYTHON_GVHMR}"
create_venv .venv-gmr "${PYTHON_GMR}"
create_venv .venv-isaac "${PYTHON_ISAAC}"

echo "[INFO] Installing tools dependencies"
"${REPO_ROOT}/.venv-tools/bin/python" -m pip install -r requirements/tools.txt -e .

bootstrap_fail=0
gvhmr_ready=1
gvhmr_version="$("${REPO_ROOT}/.venv-gvhmr/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [ "${gvhmr_version}" != "3.10" ]; then
  echo "[ERROR] GVHMR requires Python 3.10 because its upstream requirements pin a cp310 PyTorch3D wheel." >&2
  echo "[ERROR] Current .venv-gvhmr Python is ${gvhmr_version}." >&2
  echo "[ERROR] Install Python 3.10 with venv support, then run: PYTHON_GVHMR=python3.10 ./scripts/bootstrap_venvs.sh" >&2
  gvhmr_ready=0
  bootstrap_fail=1
fi

if [ "${gvhmr_ready}" -eq 1 ]; then
  echo "[INFO] Pre-installing GVHMR legacy build dependencies"
  "${REPO_ROOT}/.venv-gvhmr/bin/python" -m pip install numpy==1.23.5 scipy setuptools wheel
  "${REPO_ROOT}/.venv-gvhmr/bin/python" -m pip install --no-build-isolation chumpy==0.70
  echo "[INFO] Installing GVHMR dependencies"
  "${REPO_ROOT}/.venv-gvhmr/bin/python" -m pip install -r third_party/GVHMR/requirements.txt
  "${REPO_ROOT}/.venv-gvhmr/bin/python" -m pip install -e third_party/GVHMR
else
  echo "[WARN] Skipping GVHMR dependency install until .venv-gvhmr uses Python 3.10." >&2
fi

echo "[INFO] Installing GMR dependencies"
"${REPO_ROOT}/.venv-gmr/bin/python" -m pip install -r requirements/gmr.txt -e .

echo "[INFO] Installing Isaac wrapper dependencies"
"${REPO_ROOT}/.venv-isaac/bin/python" -m pip install -r requirements/isaac.txt -e .

echo "[INFO] Checking key imports"
"${REPO_ROOT}/.venv-tools/bin/python" -c "import numpy, yaml; import m_c_video_to_robot"
if [ "${gvhmr_ready}" -eq 1 ]; then
  "${REPO_ROOT}/.venv-gvhmr/bin/python" -c "import torch; import hmr4d"
fi
"${REPO_ROOT}/.venv-gmr/bin/python" -c "import mujoco, mink; import general_motion_retargeting; import m_c_video_to_robot"
"${REPO_ROOT}/.venv-isaac/bin/python" -c "import numpy, yaml; import m_c_video_to_robot"

if [ "${bootstrap_fail}" -ne 0 ]; then
  echo "[ERROR] Bootstrap finished with blockers listed above." >&2
  exit 1
fi
echo "[OK] All venvs are ready."
