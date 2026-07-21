#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

if ! find patches/GMR -type f -name '*.patch' | grep -q .; then
  echo "[OK] No GMR patches are required."
  exit 0
fi

for patch_file in patches/GMR/*.patch; do
  echo "[INFO] Applying ${patch_file}"
  git -C third_party/GMR apply "../../${patch_file}"
done
