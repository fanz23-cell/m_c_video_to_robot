#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "${REPO_ROOT}/.venv-tools/bin/python" -m pytest -q
