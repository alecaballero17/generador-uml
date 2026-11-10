param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{32}$')][string]$BuildId,
    [ValidateRange(1024,65535)][int]$Port = 8087
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$buildDir = Join-Path $repoRoot "output/build_$BuildId"
$status = Get-Content -LiteralPath (Join-Path $buildDir 'status.json') -Raw | ConvertFrom-Json
if ($status.state -ne 'succeeded') { throw 'La compilacion no termino correctamente. Revisa build.log.' }
$backendDir = Join-Path $buildDir 'springboot'
$jarFiles = @(Get-ChildItem -LiteralPath (Join-Path $backendDir 'target') -Filter '*.jar')
if ($jarFiles.Count -ne 1) { throw 'No se encontro un unico JAR. Vuelve a compilar desde el editor.' }
Write-Host "Backend local: http://127.0.0.1:$Port/api/health"
Write-Host 'Deja esta terminal abierta. Ctrl+C detiene solamente este backend.'
Push-Location $backendDir
try {
    & java -jar $jarFiles[0].FullName '--spring.profiles.active=demo' "--server.port=$Port"
    if ($LASTEXITCODE -ne 0) { throw "Java termino con codigo $LASTEXITCODE" }
} finally { Pop-Location }
