$taskName = "LAIS Vault Sync"
$pythonPath = (Get-Command python).Source
$scriptPath = "C:\Users\stefa\Desktop\AI projects\LAIS\models\ai_engine\vault_activate.py"
$workDir = "C:\Users\stefa\Desktop\AI projects\LAIS\models\ai_engine"

# Remove existing task if present
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Register new task - runs at user logon, restarts on failure
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`" --watch" -WorkingDirectory $workDir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "stefa"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId "stefa" -LogonType S4U -RunLevel Limited

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force

Write-Host "  Registered: $taskName"
Write-Host "  Script:     $scriptPath"
Write-Host "  Trigger:    At logon (stefa)"
Write-Host "  Python:     $pythonPath"
Write-Host ""
Write-Host "Running for first time..."
Start-ScheduledTask -TaskName $taskName
Write-Host "  Started."
Write-Host ""
Write-Host "To check: Get-ScheduledTask -TaskName '$taskName' | fl"
Write-Host "To stop:  Stop-ScheduledTask -TaskName '$taskName'"
Write-Host "To unregister: Unregister-ScheduledTask -TaskName '$taskName' -Confirm"
