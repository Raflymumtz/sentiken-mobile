# Mendaftarkan start-local-server.ps1 supaya berjalan otomatis setiap kali
# pengguna login ke Windows (Task Scheduler, trigger "At log on"). Jalankan
# skrip ini SEKALI SAJA secara manual dari PowerShell biasa (tidak perlu
# Administrator untuk task milik user sendiri).

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $RepoRoot "scripts\start-local-server.ps1"
$TaskName = "SentikenMobile-LocalServer"

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ScriptPath`""

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description "Auto-start backend + Cloudflare Tunnel SENTIKEN Mobile saat login." `
    -Force

Write-Output "Task '$TaskName' terdaftar. Backend + tunnel akan otomatis jalan tiap kali kamu login ke Windows."
Write-Output "Untuk menjalankan sekarang juga tanpa logout/login: Start-ScheduledTask -TaskName '$TaskName'"
