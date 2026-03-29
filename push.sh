#!/usr/bin/env bash
# Git Bash 用：保存后一键提交并推送到 GitHub
# 用法（在仓库任意处）:
#   bash push.sh "你的提交说明"
# 若省略说明，默认使用 update

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

MSG="${1:-update}"

git add .
git commit -m "$MSG"
git push origin main

echo "Done: pushed to origin/main"
