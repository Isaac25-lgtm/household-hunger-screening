# Run lint and the full test suite, saving a log under logs\.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$py = ".\.venv\Scripts\python.exe"
& $py -m ruff check src tests scripts dashboard
& $py -m pytest -v -p no:cacheprovider 2>&1 | Tee-Object -FilePath "logs\pytest_last.txt"
exit $LASTEXITCODE
