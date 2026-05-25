# Docker Desktop Install Guide for LAIS
# Run this script to install Docker Desktop on Windows

Write-Host "=== Docker Desktop Installer for LAIS ===" -ForegroundColor Cyan
Write-Host ""

# Check if already installed
$dockerPath = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerPath) {
    Write-Host "[OK] Docker Desktop is already installed at $dockerPath" -ForegroundColor Green
    exit 0
}

Write-Host "[+] Downloading Docker Desktop..." -ForegroundColor Yellow
$url = "https://desktop.docker.com/win/stable/Docker%20Desktop%20Installer.exe"
$out = "$env:TEMP\DockerDesktopInstaller.exe"

try {
    Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
    Write-Host "[OK] Downloaded to $out" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Download failed: $_" -ForegroundColor Red
    Write-Host "Download manually from: https://www.docker.com/products/docker-desktop/"
    exit 1
}

# Install
Write-Host "[+] Installing Docker Desktop..." -ForegroundColor Yellow
Write-Host "[!] This will open the installer GUI. Follow the prompts." -ForegroundColor Yellow
Write-Host "[!] Make sure to select 'Use WSL 2 instead of Hyper-V' when prompted." -ForegroundColor Yellow
Start-Process -FilePath $out -Wait

Write-Host ""
Write-Host "[OK] Docker Desktop installed. Now:" -ForegroundColor Green
Write-Host "  1. Start Docker Desktop from the Start Menu" -ForegroundColor Yellow
Write-Host "  2. Wait for the Docker engine to start (whale icon in system tray)" -ForegroundColor Yellow
Write-Host "  3. Open PowerShell and run: docker ps" -ForegroundColor Yellow
Write-Host "  4. Then: docker compose up -d  (in the LAIS directory)" -ForegroundColor Yellow
