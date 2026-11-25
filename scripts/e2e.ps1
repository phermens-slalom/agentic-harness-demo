# Windows entry point: .\scripts\e2e.ps1 [--keep] [--live-evals] [--from-stage N]
# Uses the repo's Python (3.13 via uv if .venv does not exist yet); all logic is in e2e.py.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$py = if (Get-Command uv -ErrorAction SilentlyContinue) { @("uv", "run", "--no-project", "--python", "3.13", "python") } else { @("python") }
& $py[0] $py[1..($py.Length - 1)] scripts/e2e.py @args
exit $LASTEXITCODE
