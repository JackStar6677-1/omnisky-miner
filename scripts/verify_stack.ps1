# OmniSky Stack Verification

$ApiBase = "http://127.0.0.1:8000"

Write-Host "=== Verifying OmniSky Stack ===" -ForegroundColor Cyan

# 1. Check API is up
Write-Host "`n[1/4] Checking API..." -ForegroundColor Yellow
try {
    $res = Invoke-RestMethod -Uri "$ApiBase/status" -Method Get -TimeoutSec 3
    Write-Host "  [OK] API responding. State: $($res.daemon_state)" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] API not reachable. Run run_all.ps1 first." -ForegroundColor Red
    exit 1
}

# 2. Test Pause
Write-Host "`n[2/4] Testing /pause..." -ForegroundColor Yellow
$body = '{"reason":"VERIFY_TEST"}'
Invoke-RestMethod -Uri "$ApiBase/pause" -Method Post -Body $body -ContentType "application/json" | Out-Null
Start-Sleep -Seconds 1
$res = Invoke-RestMethod -Uri "$ApiBase/status" -Method Get
if ($res.desired_state -eq "PAUSED") {
    Write-Host "  [OK] Pause command accepted" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Pause state not reflected" -ForegroundColor Yellow
}

# 3. Test Resume
Write-Host "`n[3/4] Testing /resume..." -ForegroundColor Yellow
Invoke-RestMethod -Uri "$ApiBase/resume" -Method Post | Out-Null
Start-Sleep -Seconds 1
$res = Invoke-RestMethod -Uri "$ApiBase/status" -Method Get
if ($res.desired_state -eq "RUNNING") {
    Write-Host "  [OK] Resume command accepted" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Resume state not reflected" -ForegroundColor Yellow
}

# 4. Test Events
Write-Host "`n[4/4] Testing /events..." -ForegroundColor Yellow
try {
    $evts = Invoke-RestMethod -Uri "$ApiBase/events?limit=5" -Method Get
    Write-Host "  [OK] Retrieved $($evts.Count) events" -ForegroundColor Green
} catch {
    Write-Host "  [WARN] Events endpoint error" -ForegroundColor Yellow
}

Write-Host "`n=== Verification Complete ===" -ForegroundColor Cyan
