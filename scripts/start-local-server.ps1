# Menjalankan backend SENTIKEN Mobile + Cloudflare Tunnel di laptop lokal,
# lalu memperbarui mobile/remote-config.json (di GitHub) dengan URL tunnel
# yang baru. Dengan begitu, aplikasi mobile (APK yang sudah terpasang di HP)
# otomatis memakai URL terbaru saat dibuka -- tanpa perlu build/instal ulang.
#
# Dipasang untuk berjalan otomatis lewat Task Scheduler ("At log on") supaya
# tidak perlu dijalankan manual tiap kali laptop restart. Lihat
# scripts/register-startup-task.ps1 untuk pendaftaran task-nya.

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$MobileDir = Join-Path $RepoRoot "mobile"
$JavaHome = "C:\Program Files\Android\Android Studio\jbr"
$CloudflaredExe = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$LogDir = Join-Path $BackendDir "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-BackendHealthy {
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3 -UseBasicParsing
        return $resp.StatusCode -eq 200
    } catch {
        return $false
    }
}

# 1) Jalankan backend (uvicorn) kalau belum jalan.
if (-not (Test-BackendHealthy)) {
    Write-Output "Backend belum jalan, memulai uvicorn..."
    $pythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"
    Start-Process -FilePath $pythonExe `
        -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
        -WorkingDirectory $BackendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir "uvicorn.out.log") `
        -RedirectStandardError (Join-Path $LogDir "uvicorn.err.log")

    $attempts = 0
    while (-not (Test-BackendHealthy) -and $attempts -lt 30) {
        Start-Sleep -Seconds 2
        $attempts++
    }
    if (-not (Test-BackendHealthy)) {
        throw "Backend gagal start dalam 60 detik. Cek $LogDir\uvicorn.err.log"
    }
    Write-Output "Backend siap."
} else {
    Write-Output "Backend sudah jalan."
}

# 2) Hentikan cloudflared lama (kalau ada) supaya tidak dobel tunnel.
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force

# 3) Jalankan cloudflared quick tunnel, tangkap URL barunya dari log.
$TunnelOutLog = Join-Path $LogDir "cloudflared.out.log"
$TunnelErrLog = Join-Path $LogDir "cloudflared.err.log"
Remove-Item $TunnelOutLog, $TunnelErrLog -ErrorAction SilentlyContinue
# Catatan: --logfile TIDAK dipakai karena argumennya terpotong bila path
# proyek mengandung spasi (mis. "Task A6444 Sistem Informasi"). Redirect
# stream stdout/stderr di bawah ini tidak bermasalah dengan spasi.
Start-Process -FilePath $CloudflaredExe `
    -ArgumentList "tunnel", "--url", "http://localhost:8000" `
    -WindowStyle Hidden `
    -RedirectStandardOutput $TunnelOutLog `
    -RedirectStandardError $TunnelErrLog

$tunnelUrl = $null
$attempts = 0
while (-not $tunnelUrl -and $attempts -lt 30) {
    Start-Sleep -Seconds 2
    foreach ($logFile in @($TunnelErrLog, $TunnelOutLog)) {
        if (-not $tunnelUrl -and (Test-Path $logFile)) {
            $match = Select-String -Path $logFile -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($match) { $tunnelUrl = $match.Matches[0].Value }
        }
    }
    $attempts++
}
if (-not $tunnelUrl) {
    throw "Gagal mendapatkan URL tunnel dalam 60 detik. Cek $TunnelErrLog"
}
Write-Output "Tunnel URL: $tunnelUrl"

# 4) Update mobile/remote-config.json lalu commit + push ke GitHub.
$configPath = Join-Path $MobileDir "remote-config.json"
$timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
$json = @{ api_url = "$tunnelUrl/api/v1"; updated_at = $timestamp } | ConvertTo-Json
# Set-Content -Encoding utf8 di Windows PowerShell 5.1 menulis BOM (byte
# 0xEF 0xBB 0xBF) di awal file, yang membuat JSON.parse gagal di sisi
# aplikasi mobile (JavaScript tidak menerima BOM di awal JSON). Pakai
# System.IO.File langsung dengan encoding UTF-8 tanpa BOM.
[System.IO.File]::WriteAllText($configPath, $json, (New-Object System.Text.UTF8Encoding($false)))

Push-Location $RepoRoot
git add mobile/remote-config.json
$hasChanges = (git status --porcelain mobile/remote-config.json)
if ($hasChanges) {
    git commit -m "chore: update remote-config.json ($timestamp)" | Out-Null
    git push | Out-Null
    Write-Output "remote-config.json diperbarui & di-push ke GitHub."
} else {
    Write-Output "URL tunnel sama seperti sebelumnya, tidak ada perubahan untuk di-push."
}
Pop-Location

Write-Output "Selesai. Backend + tunnel siap dipakai aplikasi mobile."
