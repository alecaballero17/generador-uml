param([int]$Port = 8765)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
$env:UML_LOCAL_BUILD = '1'
Write-Host "Editor local y compilador APK: http://127.0.0.1:$Port"
Write-Host 'Mantén esta terminal abierta. Usa Generar > Generar y compilar APK (local).'
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port $Port
