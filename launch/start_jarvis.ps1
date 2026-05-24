# Start JARVIS Voice AI only
$LAIS_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$jarvisPath = Join-Path $LAIS_ROOT "models\Mark-XXXIX\main.py"

if (Test-Path $jarvisPath) {
    Write-Host "Starting JARVIS Mark XXXIX..." -ForegroundColor Cyan
    python "`"$jarvisPath`""
} else {
    Write-Host "JARVIS not found at $jarvisPath" -ForegroundColor Red
}
