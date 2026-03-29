# 一键：git add / commit / push（在仓库根目录执行）
# 用法:
#   .\push.ps1 -Message "你的提交说明"
#   .\push.ps1                    # 默认提交信息为 update

param(
    [string]$Message = "update"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

git add .
git commit -m $Message
git push origin main

Write-Host "Done: pushed to origin/main" -ForegroundColor Green
