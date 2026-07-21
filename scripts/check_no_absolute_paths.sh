#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

pattern="/home/"
pattern="${pattern}mindbot"

if grep -RIn \
  --exclude-dir=.git \
  --exclude-dir=.venv-gvhmr \
  --exclude-dir=.venv-gmr \
  --exclude-dir=.venv-tools \
  --exclude-dir=.venv-isaac \
  "${pattern}" .; then
  echo "[ERROR] Found local absolute paths in repository files." >&2
  exit 1
fi

echo "[OK] No local absolute paths found."
