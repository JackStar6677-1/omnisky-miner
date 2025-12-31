$Action = New-ScheduledTaskAction -Execute "pythonw.exe" -Argument "..\services\daemon.py" -WorkingDirectory "$PSScriptRoot"
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName "OmniSkyDaemon" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal

Write-Host "✅ OmniSky Daemon registered to start at Login."
Write-Host "   To start now: Start-ScheduledTask -TaskName 'OmniSkyDaemon'"
