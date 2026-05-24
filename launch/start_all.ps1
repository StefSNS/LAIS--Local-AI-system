# LAIS — Start All Agents
$LAIS_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "Starting LAIS..." -ForegroundColor Cyan

# 1. AI Engine GUI (background)
$aiPath = Join-Path $LAIS_ROOT "models\ai_engine\main.py"
if (Test-Path $aiPath) {
    Write-Host "  [AI Engine] Starting..." -ForegroundColor Yellow
    Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "`"$aiPath`""
    Start-Sleep -Seconds 2
}

# 2. JARVIS voice AI
$jarvisPath = Join-Path $LAIS_ROOT "models\Mark-XXXIX\main.py"
if (Test-Path $jarvisPath) {
    Write-Host "  [JARVIS] Starting..." -ForegroundColor Yellow
    Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "`"$jarvisPath`""
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "LAIS agents started:" -ForegroundColor Green
Write-Host "  - AI Engine GUI (models/ai_engine/main.py)" -ForegroundColor Green
Write-Host "  - JARVIS Voice AI (models/Mark-XXXIX/main.py)" -ForegroundColor Green
Write-Host ""
Write-Host "For OpenCode: python $LAIS_ROOT\lais_opencode.py" -ForegroundColor Yellow
