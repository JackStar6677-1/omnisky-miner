# OmniSky Command Center - Run All Services
# Usage: .\run_all.ps1

$Root = Split-Path $PSScriptRoot -Parent
$DataDir = Join-Path $Root "OMNISKY_DATA\OBS"

# Ensure Data Dir
if (-not (Test-Path $DataDir)) { New-Item -ItemType Directory -Path $DataDir -Force | Out-Null }

Write-Host "=== OmniSky Command Center ===" -ForegroundColor Cyan

# 1. Start Python Daemon (Core)
Write-Host "`n[1/3] Starting Python Daemon..." -ForegroundColor Yellow
$DaemonPath = Join-Path $Root "services\daemon.py"
Start-Process -FilePath "pythonw" -ArgumentList $DaemonPath -WorkingDirectory $Root -WindowStyle Hidden
Write-Host "  > Daemon started (background)"

# 2. Start FastAPI
Write-Host "`n[2/3] Starting FastAPI Server..." -ForegroundColor Yellow
$ApiPath = Join-Path $Root "api\app.py"
# Check for venv
$VenvPython = Join-Path $Root "venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    Start-Process -FilePath $VenvPython -ArgumentList "-m uvicorn app:app --reload --host 127.0.0.1 --port 8000" -WorkingDirectory (Join-Path $Root "api")
} else {
    Start-Process -FilePath "python" -ArgumentList "-m uvicorn app:app --reload --host 127.0.0.1 --port 8000" -WorkingDirectory (Join-Path $Root "api")
}
Write-Host "  > API at http://127.0.0.1:8000"

# 3. Serve UI (static for now)
Write-Host "`n[3/3] UI Ready" -ForegroundColor Yellow
$UiPath = Join-Path $Root "ui\index.html"
if (Test-Path $UiPath) {
    Write-Host "  > Open UI: file:///$UiPath" -ForegroundColor Green
    Write-Host "  > Or access via API: http://127.0.0.1:8000/ui" -ForegroundColor Green
} else {
    Write-Host "  > UI not found. Run build_all.ps1 first." -ForegroundColor Red
}

Write-Host "`n=== All Services Running ===" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop (or close this window)"
