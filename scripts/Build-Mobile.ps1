param([switch]$Install)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$androidRoot=Join-Path $taskRoot 'mobile-android'
$assetRoot=Join-Path $androidRoot 'app\src\main\assets'
New-Item -ItemType Directory -Force $assetRoot | Out-Null
Copy-Item -Path (Join-Path $taskRoot 'frontend\*') -Destination $assetRoot -Recurse -Force
$env:JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
& (Join-Path $androidRoot 'gradlew.bat') -p $androidRoot assembleDebug --console=plain
if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar el graficador Android.' }
$apkPath=Join-Path $androidRoot 'app\build\outputs\apk\debug\app-debug.apk'
Write-Output $apkPath
if ($Install) {
 & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install -r $apkPath
 if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar el APK por USB.' }
}
