param([switch]$Open)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$runtime = Join-Path $projectRoot '.runtime'
New-Item -ItemType Directory -Force $runtime | Out-Null
function Test-LocalService([string]$Url) {
    try { (Invoke-WebRequest $Url -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200 } catch { $false }
}
function Start-DemoProcess([string]$Name,[string]$Command,[string]$Directory) {
    $jobFile = Join-Path $runtime "$Name.ps1"
    Set-Content -LiteralPath $jobFile -Value $Command -Encoding UTF8
    $process = Start-Process powershell.exe -ArgumentList @('-NoProfile','-File',('"' + $jobFile + '"')) -WorkingDirectory $Directory -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtime "$Name.log") -RedirectStandardError (Join-Path $runtime "$Name-error.log") -PassThru
    Set-Content (Join-Path $runtime "$Name.pid") $process.Id
}
$pgBin = 'C:\Program Files\PostgreSQL\16\bin'
$cluster = Join-Path $runtime 'postgres-demo'
if (!(Test-Path (Join-Path $cluster 'PG_VERSION'))) { throw 'Falta la base de datos de demostracion preparada. Consulte docs/estado-verificacion.md.' }
& "$pgBin\pg_ctl.exe" -D $cluster status *> $null
if ($LASTEXITCODE -ne 0) {
    & "$pgBin\pg_ctl.exe" -D $cluster -l (Join-Path $runtime 'postgres.log') -o '-h 127.0.0.1 -p 55432' start
    if ($LASTEXITCODE -ne 0) { throw 'No pudo arrancar PostgreSQL de demostracion.' }
}
if (!(Test-LocalService 'http://127.0.0.1:8765/api/health')) {
    $python = Join-Path $projectRoot '.venv\Scripts\python.exe'
    $backend = Join-Path $projectRoot 'backend'
    Start-DemoProcess 'editor' "& '$python' -m uvicorn app.main:app --app-dir '$backend' --host 127.0.0.1 --port 8765" $projectRoot
}
if (!(Test-LocalService 'http://127.0.0.1:8080/api/health')) {
    $maven = Join-Path $env:USERPROFILE '.maven\apache-maven-3.9.9\bin\mvn.cmd'
    $repo = Join-Path $env:USERPROFILE '.m2\repository'
    $spring = Join-Path $projectRoot 'output\verification_20260917\cursos\springboot'
    $command = @"
`$env:SPRING_DATASOURCE_URL='jdbc:postgresql://127.0.0.1:55432/cursos_demo'
`$env:SPRING_DATASOURCE_USERNAME='uml_demo'
`$env:SPRING_DATASOURCE_PASSWORD=''
`$env:SERVER_ADDRESS='127.0.0.1'
`$env:SERVER_PORT='8080'
& '$maven' -B '-Dmaven.repo.local=$repo' spring-boot:run
"@
    Start-DemoProcess 'cursos-backend' $command $spring
}
if (!(Test-LocalService 'http://127.0.0.1:8090/')) {
    $flutter = 'C:\src\flutter\bin\flutter.bat'
    $app = Join-Path $projectRoot 'output\verification_20260917\cursos\flutter_app'
    Start-DemoProcess 'cursos-web' "& '$flutter' run -d web-server --web-hostname 127.0.0.1 --web-port 8090 --no-pub" $app
}
Write-Host 'Procesos iniciados. El primer arranque puede tardar. Logs en .runtime.'
Write-Host 'Editor: http://127.0.0.1:8765/'
Write-Host 'Aplicacion Flutter de cursos: http://127.0.0.1:8090/'
if ($Open) { Start-Process 'http://127.0.0.1:8765/'; Start-Process 'http://127.0.0.1:8090/' }
