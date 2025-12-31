# OmniSky Command Center - Build All Components

$Root = Split-Path $PSScriptRoot -Parent

Write-Host "=== Building OmniSky Stack ===" -ForegroundColor Cyan

# 1. Python venv + deps
Write-Host "`n[1/3] Setting up Python environment..." -ForegroundColor Yellow
$VenvPath = Join-Path $Root "venv"
if (-not (Test-Path $VenvPath)) {
    python -m venv $VenvPath
}
& "$VenvPath\Scripts\pip" install -r (Join-Path $Root "requirements.txt") -q
& "$VenvPath\Scripts\pip" install -r (Join-Path $Root "api\requirements.txt") -q
Write-Host "  > Python deps installed"

# 2. UI (if npm available)
Write-Host "`n[2/3] Building UI..." -ForegroundColor Yellow
$UiPath = Join-Path $Root "ui"
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Push-Location $UiPath
    npm install 2>$null
    npm run build 2>$null
    Pop-Location
    Write-Host "  > UI built to ui/dist"
} else {
    Write-Host "  > npm not found. UI will run from source."
}

# 3. C# Agent
Write-Host "`n[3/3] Building C# Agent..." -ForegroundColor Yellow
$AgentProj = Join-Path $Root "agent-win\OmniSky.Agent\OmniSky.Agent.csproj"
if (Get-Command dotnet -ErrorAction SilentlyContinue) {
    dotnet build $AgentProj -c Release -o (Join-Path $Root "dist\agent") 2>$null
    Write-Host "  > Agent built to dist/agent"
} else {
    Write-Host "  > dotnet not found. Skipping agent build."
}

Write-Host "`n=== Build Complete ===" -ForegroundColor Cyan
