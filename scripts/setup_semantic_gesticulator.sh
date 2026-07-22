#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_SEMANTIC="${PYTHON_SEMANTIC:-python3.12}"
SG_ROOT="${SEMANTIC_GESTICULATOR_ROOT:-${REPO_ROOT}/third_party/Semantic-Gesticulator-Official}"
SG_URL="https://github.com/LuMen-ze/Semantic-Gesticulator-Official.git"

if [ ! -d "${SG_ROOT}/.git" ]; then
  mkdir -p "$(dirname "${SG_ROOT}")"
  git clone "${SG_URL}" "${SG_ROOT}"
else
  echo "[OK] Semantic-Gesticulator already exists: ${SG_ROOT}"
fi

if [ ! -x ".venv-semantic/bin/python" ]; then
  "${PYTHON_SEMANTIC}" -m venv .venv-semantic
fi

".venv-semantic/bin/python" -m pip install --upgrade pip setuptools wheel
".venv-semantic/bin/python" -m pip install -r "${SG_ROOT}/SG_code/requirements.txt"

cat <<'EOF'

[OK] Semantic-Gesticulator code and .venv-semantic are ready.

Next, download the official Semantic-Gesticulator assets and place them here:

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

The processed dataset assets must also exist under:

  third_party/Semantic-Gesticulator-Official/SG_code/Data/SG_processed/

EOF
