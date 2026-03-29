#!/usr/bin/env pwsh
# Launcher script for Genshin Impact Rich Presence using embedded Python

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "Starting Genshin Impact Rich Presence..." -ForegroundColor Green
Write-Host "Using embedded Python: python3.13.11_embedded\python.exe" -ForegroundColor Cyan
Write-Host ""

& ".\python3.13.11_embedded\python.exe" "main.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error occurred. Press any key to exit..." -ForegroundColor Red
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
