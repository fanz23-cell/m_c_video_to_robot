#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/check_no_absolute_paths.sh
git status --short
git diff --check

if ! gh auth status >/dev/null 2>&1; then
  echo "[ERROR] GitHub CLI is not logged in. Run: gh auth login" >&2
  exit 1
fi

GH_OWNER="$(gh api user --jq .login)"
repo="${GH_OWNER}/m_c_video_to_robot"

if gh repo view "${repo}" >/dev/null 2>&1; then
  if ! git remote get-url origin >/dev/null 2>&1; then
    git remote add origin "https://github.com/${repo}.git"
  fi
else
  gh repo create m_c_video_to_robot --private --source=. --remote=origin
fi

git add .
git commit -m "Initial video-to-robot retargeting pipeline"
git branch -M main
git push -u origin main
gh repo view --web
