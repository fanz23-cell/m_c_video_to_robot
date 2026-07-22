#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

if ! find patches/GVHMR -type f -name '*.patch' | grep -q .; then
  echo "[OK] No GVHMR patches are required."
  exit 0
fi

for patch_file in patches/GVHMR/*.patch; do
  echo "[INFO] Applying ${patch_file}"
  if [ "$(basename "${patch_file}")" = "blackwell_cu128_demo.patch" ] \
    && grep -q "register_store_gvhmr_demo" third_party/GVHMR/hmr4d/configs/__init__.py \
    && grep -q -- "--no_render" third_party/GVHMR/tools/demo/demo.py; then
    echo "[INFO] ${patch_file} is already applied."
    continue
  fi
  if git -C third_party/GVHMR apply --check "../../${patch_file}" 2>/dev/null; then
    git -C third_party/GVHMR apply "../../${patch_file}"
  else
    echo "[ERROR] ${patch_file} cannot be applied cleanly." >&2
    exit 1
  fi
done
