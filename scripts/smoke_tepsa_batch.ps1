#Requires -Version 5.1
<#
.SYNOPSIS
  Preflight + optional three-vendor API smoke (TEPSA batch).

  Set OPENAI_API_KEY, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY in the session (or system) before running.
  Do not commit secrets. Run from repo root: .\scripts\smoke_tepsa_batch.ps1
#>
$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))

python src/tepsa_validate_inputs.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python src/tepsa_api_batch.py --dry-run
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$runId = "smoke20260201"
$need = @("OPENAI_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY")
$missing = @(
  $need | Where-Object {
    [string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($_, "Process"))
  }
)
if ($missing.Count -gt 0) {
  Write-Host "Skip API smoke: missing env: $($missing -join ', ')" -ForegroundColor Yellow
  Write-Host "When keys are set, run:" -ForegroundColor Yellow
  Write-Host "  python src/tepsa_api_batch.py --run-id $runId --max-tasks 1 --policy-ids pl_openai_mini_std --providers OpenAI"
  Write-Host "  python src/tepsa_api_batch.py --run-id $runId --max-tasks 1 --policy-ids pl_deepseek_flash --providers DeepSeek"
  Write-Host "  python src/tepsa_api_batch.py --run-id $runId --max-tasks 1 --policy-ids pl_claude_haiku --providers Anthropic"
  exit 0
}

python src/tepsa_api_batch.py --run-id $runId --max-tasks 1 --policy-ids pl_openai_mini_std --providers OpenAI
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python src/tepsa_api_batch.py --run-id $runId --max-tasks 1 --policy-ids pl_deepseek_flash --providers DeepSeek
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python src/tepsa_api_batch.py --run-id $runId --max-tasks 1 --policy-ids pl_claude_haiku --providers Anthropic
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Smoke done. Check data/tessa_psa/task_policy_observations.csv and data/tessa_psa/runs/$runId/" -ForegroundColor Green
