# Install OmniSky Agent to run at startup

$AgentPath = Join-Path $PSScriptRoot "..\agent-win\OmniSky.Agent\bin\Release\net8.0-windows\OmniSkyAgent.exe"

if (-not (Test-Path $AgentPath)) {
    Write-Host "Agent not built. Run build_all.ps1 first."
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $AgentPath
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "OmniSkyAgent" -Action $Action -Trigger $Trigger -Settings $Settings -Force

Write-Host "OmniSky Agent installed. Will start at next login."
