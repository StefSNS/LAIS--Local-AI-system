# LAIS One-Line Installer
# Run: powershell -c "irm https://raw.githubusercontent.com/StefSNS/LAIS/main/install.ps1 | iex"

$ErrorActionPreference = "Stop"
$LAIS_DIR = Join-Path $env:USERPROFILE "LAIS"

Write-Host "=== LAIS — Local AI System Installer ===" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
$pythonOK = $false
try {
    $pyVersion = python --version 2>&1
    if ($pyVersion -match "3\.(1[1-9]|[2-9]\d)") { $pythonOK = $true }
} catch {}
if (-not $pythonOK) {
    Write-Host "[!] Python 3.11+ required. Download from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python: $((python --version 2>&1))" -ForegroundColor Green

$gitOK = $false
try { $gitOK = git --version 2>$null } catch {}
if (-not $gitOK) {
    Write-Host "[!] Git not found. Install from https://git-scm.com" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Git found" -ForegroundColor Green

# Clone or update
if (Test-Path $LAIS_DIR) {
    Write-Host "[!] LAIS already installed at $LAIS_DIR" -ForegroundColor Yellow
    $update = Read-Host "Update? (Y/n)"
    if ($update -ne "n") {
        Set-Location -LiteralPath $LAIS_DIR
        git pull
        Write-Host "[OK] Updated" -ForegroundColor Green
    }
} else {
    Write-Host "[+] Downloading LAIS..." -ForegroundColor Yellow
    git clone --depth 1 https://github.com/StefSNS/LAIS.git $LAIS_DIR
    Write-Host "[OK] Downloaded to $LAIS_DIR" -ForegroundColor Green
}

# Run installer
Set-Location -LiteralPath $LAIS_DIR
python install.py

Write-Host ""
Write-Host "=== LAIS Installation Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. cd $LAIS_DIR" -ForegroundColor Yellow
Write-Host "  2. Edit models/Mark-XXXIX/config/api_keys.json with your Gemini API key" -ForegroundColor Yellow
Write-Host "  3. Run: python models/Mark-XXXIX/main.py     (JARVIS)" -ForegroundColor Yellow
Write-Host "  4. Run: python models/ai_engine/main.py      (AI Engine)" -ForegroundColor Yellow
Write-Host "  5. Run: python lais_opencode.py              (OpenCode)" -ForegroundColor Yellow
Write-Host ""
