# LAIS - Start All Agents
Write-Host "=== LAIS Launcher ===" -ForegroundColor Cyan

function Start-Agent {
    param($Name, $Path, $Entry)
    $fullPath = Join-Path $PSScriptRoot ".." $Path
    if (Test-Path (Join-Path $fullPath $Entry)) {
        Write-Host "Starting $Name..." -ForegroundColor Green
        $job = Start-Job -ScriptBlock {
            param($p, $e)
            Set-Location $p
            python $e
        } -ArgumentList $fullPath, $Entry
        return $job
    } else {
        Write-Host "WARNING: $Name not found at $fullPath\$Entry" -ForegroundColor Yellow
        return $null
    }
}

$config = Get-Content (Join-Path $PSScriptPoint ".." "config" "system.json") | ConvertFrom-Json

$jobs = @()
$jobs += Start-Agent -Name "JARVIS" -Path $config.models.mark-xxxv.path -Entry $config.models.mark-xxxv.entry
$jobs += Start-Agent -Name "AI Engine" -Path $config.models.ai_engine.path -Entry $config.models.ai_engine.entry

Write-Host "`nAll agents launched. Monitoring..." -ForegroundColor Cyan
$jobs | Where-Object { $_ -ne $null } | Wait-Job
