param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{32}$')][string]$BuildId,
    [string]$DeviceSerial,
    [ValidateRange(1024,65535)][int]$Port = 8087
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$buildDir = Join-Path $repoRoot "output/build_$BuildId"
$status = Get-Content -LiteralPath (Join-Path $buildDir 'status.json') -Raw | ConvertFrom-Json
if ($status.state -ne 'succeeded') { throw 'La compilacion no termino correctamente.' }
$apkPath = Join-Path $buildDir 'aplicacion.apk'
if (!(Test-Path -LiteralPath $apkPath)) { throw 'No se encontro aplicacion.apk.' }
$adbCommand = Get-Command adb -ErrorAction SilentlyContinue
$adbPath = if ($adbCommand) { $adbCommand.Source } else { Join-Path $env:LOCALAPPDATA 'Android/sdk/platform-tools/adb.exe' }
if (!(Test-Path -LiteralPath $adbPath)) { throw 'Instala Android SDK Platform Tools antes de continuar.' }
$deviceLines = & $adbPath devices
if ($LASTEXITCODE -ne 0) { throw 'No se pudo consultar adb.' }
$serials = @($deviceLines | ForEach-Object { if ($_ -match '^(\S+)\s+device$') { $Matches[1] } })
if (!$DeviceSerial) {
    if ($serials.Count -ne 1) { throw 'Conecta y autoriza un telefono USB. Si hay varios, especifica -DeviceSerial.' }
    $DeviceSerial = $serials[0]
}
if ($DeviceSerial -notin $serials) { throw 'El dispositivo no esta conectado o no autorizo la depuracion USB.' }
$health = Invoke-RestMethod "http://127.0.0.1:$Port/api/health"
if ($health.status -ne 'UP') { throw 'Inicia primero el backend generado con Start-Generated.ps1.' }
& $adbPath -s $DeviceSerial reverse "tcp:$Port" "tcp:$Port"
if ($LASTEXITCODE -ne 0) { throw 'No se pudo establecer la conexion USB al backend.' }
& $adbPath -s $DeviceSerial install -r $apkPath
if ($LASTEXITCODE -ne 0) { throw 'Android no pudo instalar la APK. Conserva el mensaje de error.' }
Write-Host "Abre la app instalada y configura su servidor como http://127.0.0.1:$Port/api"
Write-Host 'Verifica crear, listar, editar y eliminar un registro. Instalar no verifica todavia el CRUD en el telefono.'
