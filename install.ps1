# LAIS One-Line Installer
# Run: powershell -c "irm https://raw.githubusercontent.com/StefSNS/LAIS--Local-AI-system/main/install.ps1 | iex"
# Requires: Windows 10+, Python 3.11+, Git

param(
    [switch]$Quick,
    [string]$Dir = (Join-Path $env:USERPROFILE "LAIS")
)

$REPO_URL = "https://github.com/StefSNS/LAIS--Local-AI-system.git"
$RAW_URL  = "https://raw.githubusercontent.com/StefSNS/LAIS--Local-AI-system/main"

function step($msg) { Write-Host "`n  >>> $msg`n  $('='*60)" -ForegroundColor Cyan }
function ok($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function warn($msg) { Write-Host "  [!] $msg" -ForegroundColor Yellow }
function fail($msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red; exit 1 }

Write-Host @"

  ============================================================
         LAIS - Local AI System  v2.0.0
         Voice AI + GUI Orchestrator + CLI Coder
  ============================================================

"@ -ForegroundColor Cyan

# Phase 1: Prerequisites
step "Phase 1/5: Checking Prerequisites"
try {
    $ver = python --version 2>&1
    if ($ver -match "3\.(1[1-9]|[2-9]\d)") { ok "Python $ver" }
    else { fail "Python 3.11+ required, found $ver" }
} catch { fail "Python not found. Install from https://python.org" }

try { $null = git --version 2>&1; ok "Git found" }
catch { fail "Git not found. Install from https://git-scm.com" }

try {
    $disk = (Get-PSDrive ($Dir -split ':\\')[0] -ErrorAction Stop).Free / 1MB
    if ($disk -lt 500) { fail "Need 500MB free, only ${disk}MB available" }
    ok "Disk space: $([math]::Round($disk))MB free"
} catch { warn "Could not check disk space" }

# Phase 2: Download
step "Phase 2/5: Downloading LAIS"
if (Test-Path $Dir) {
    warn "LAIS already installed at $Dir"
    if (-not $Quick) {
        $resp = Read-Host "Update existing installation? (Y/n)"
        if ($resp -eq "n") { Write-Host "Exiting."; exit 0 }
    }
    Push-Location -LiteralPath $Dir
    git pull
    if ($LASTEXITCODE -ne 0) { fail "Update failed" }
    ok "Updated to latest version"
    Pop-Location
} else {
    Write-Host "  Cloning to $Dir ..."
    git clone --depth 1 $REPO_URL $Dir 2>&1 | ForEach-Object { Write-Host "  $_" }
    if ($LASTEXITCODE -ne 0) { fail "Clone failed" }
    ok "Downloaded to $Dir"
}

# Phase 3: Python installer
step "Phase 3/5: Running Python Installer"
Push-Location -LiteralPath $Dir
if ($Quick) { python install.py --quick }
else        { python install.py }
if ($LASTEXITCODE -ne 0) { fail "Installer exited with code $LASTEXITCODE" }
Pop-Location

# Phase 4: Environment check
step "Phase 4/5: Environment Check"
$hasKeys = $false
$keyFile = Join-Path $Dir "models\Mark-XXXIX\config\api_keys.json"
if (Test-Path $keyFile) {
    $content = Get-Content -Path $keyFile -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($content.gemini_api_key -and $content.gemini_api_key -ne "your-gemini-api-key-here") { $hasKeys = $true }
}
if ($hasKeys) { ok "Gemini API key configured" }
else { warn "Gemini API key not set. Edit: $keyFile" }

# Phase 5: Summary
step "Phase 5/5: Installation Summary"
Write-Host @"
  Location: $Dir
  Size:     $([math]::Round((Get-ChildItem -Path $Dir -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB))MB

  Next steps:
    1. cd $Dir
    2. Set your Gemini API key in models/Mark-XXXIX/config/api_keys.json
    3. Run agents:
       python models/Mark-XXXIX/main.py            (JARVIS voice AI)
       python models/ai_engine/main.py              (AI Engine GUI)
       python lais_opencode.py                       (OpenCode CLI)

  Docs:  $RAW_URL/README.md
  Repo:  $REPO_URL
"@ -ForegroundColor Cyan
