# Create the project virtual environment inside the project folder and install pinned dependencies.
# Usage (from the project root):  powershell -ExecutionPolicy Bypass -File scripts\bootstrap_environment.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
if (-not (Test-Path ".venv")) { python -m venv .venv }
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements-lock.txt
& ".\.venv\Scripts\python.exe" -m pip install -e . --no-deps
Write-Host "Environment ready: .venv"
