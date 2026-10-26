# Full reproducible run: acquire + verify source, analysis, figures, tables, dashboard data, tests, safety audit.
# Usage (from the project root):  powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$py = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Run scripts\bootstrap_environment.ps1 first." }

& $py -m hunger_screening.cli all
if ($LASTEXITCODE -ne 0) { throw "Pipeline failed (exit $LASTEXITCODE). See logs\pipeline.log" }

& $py -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed (exit $LASTEXITCODE)." }

& $py scripts\check_release_safety.py
if ($LASTEXITCODE -ne 0) { throw "Release-safety audit failed." }
Write-Host "All steps completed."
