# Launch the dashboard locally (bound to this machine only) at http://localhost:8501
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
& ".\.venv\Scripts\python.exe" -m streamlit run dashboard\app.py --server.address localhost --server.port 8501 --browser.gatherUsageStats false
