#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

fail=0

check_file() {
  if [ ! -e "$1" ]; then
    echo "[ERROR] Missing $1" >&2
    fail=1
  else
    echo "[OK] $1"
  fi
}

check_file "third_party/GVHMR/README.md"
check_file "third_party/GMR/README.md"
check_file ".env.example"

tools_python=""
for venv in .venv-tools .venv-gvhmr .venv-gmr .venv-isaac; do
  if [ -x "${venv}/bin/python" ]; then
    echo "[OK] ${venv}"
    if [ "${venv}" = ".venv-tools" ]; then
      tools_python="${venv}/bin/python"
    fi
  else
    echo "[WARN] ${venv} missing; run ./scripts/bootstrap_venvs.sh"
    fail=1
  fi
done

if [ -n "${tools_python}" ]; then
  "${REPO_ROOT}/${tools_python}" -c "import numpy, yaml; import m_c_video_to_robot" || {
    echo "[ERROR] .venv-tools import check failed." >&2
    fail=1
  }
  "${REPO_ROOT}/${tools_python}" scripts/inspect_official_environment.py >/dev/null 2>&1 || {
    echo "[WARN] Could not inspect official Isaac environment with .venv-tools." >&2
    fail=1
  }
fi

if [ -x ".venv-gvhmr/bin/python" ]; then
  gvhmr_version="$(.venv-gvhmr/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if [ "${gvhmr_version}" != "3.10" ]; then
    echo "[ERROR] .venv-gvhmr uses Python ${gvhmr_version}; GVHMR needs Python 3.10." >&2
    fail=1
  else
    .venv-gvhmr/bin/python -c "import torch; import hmr4d" || {
      echo "[ERROR] .venv-gvhmr import check failed." >&2
      fail=1
    }
  fi
fi

if [ -x ".venv-gmr/bin/python" ]; then
  .venv-gmr/bin/python -c "import mujoco, mink; import general_motion_retargeting; import m_c_video_to_robot" || {
    echo "[ERROR] .venv-gmr import check failed." >&2
    fail=1
  }
fi

if [ -x ".venv-isaac/bin/python" ]; then
  .venv-isaac/bin/python -c "import numpy, yaml; import m_c_video_to_robot" || {
    echo "[ERROR] .venv-isaac import check failed." >&2
    fail=1
  }
fi

if [ "${fail}" -ne 0 ]; then
  exit 1
fi
echo "[OK] Dependency check passed."
