$ErrorActionPreference = "Stop"

$Version = "4.5.12"
$BaseUrl = "https://download.blender.org/release/Blender4.5"
$Archive = "blender-$Version-windows-x64.zip"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ToolsDir = Join-Path $Root ".tools\blender"
$InstallDir = Join-Path $ToolsDir $Version
$CacheDir = Join-Path $Root ".cache\blender"
$ReportDir = Join-Path $Root "artifacts\blender_reports"
$BlenderExe = Join-Path $InstallDir "blender.exe"

New-Item -ItemType Directory -Force -Path $ToolsDir, $CacheDir, $ReportDir | Out-Null

if (-not (Test-Path $BlenderExe)) {
    $ArchivePath = Join-Path $CacheDir $Archive
    $ManifestPath = Join-Path $CacheDir "blender-$Version.sha256"

    Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/$Archive" -OutFile $ArchivePath
    Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/blender-$Version.sha256" -OutFile $ManifestPath

    $ManifestLine = Get-Content $ManifestPath | Where-Object { $_ -match [regex]::Escape($Archive) }
    if (-not $ManifestLine) { throw "Checksum oficial não encontrado para $Archive" }
    $Expected = ($ManifestLine -split '\s+')[0].ToLowerInvariant()
    $Actual = (Get-FileHash -Algorithm SHA256 $ArchivePath).Hash.ToLowerInvariant()
    if ($Expected -ne $Actual) { throw "SHA-256 inválido para $Archive" }

    $TempDir = Join-Path $ToolsDir ".extract-$Version"
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $TempDir, $InstallDir
    Expand-Archive -Path $ArchivePath -DestinationPath $TempDir -Force
    $Extracted = Get-ChildItem -Directory $TempDir | Select-Object -First 1
    if (-not $Extracted) { throw "Diretório extraído não encontrado" }
    Move-Item $Extracted.FullName $InstallDir
    Remove-Item -Recurse -Force $TempDir
}

& $BlenderExe --version
& $BlenderExe `
    --background `
    --factory-startup `
    --disable-autoexec `
    --python-exit-code 1 `
    --python (Join-Path $Root "blender_env\scripts\verify_environment.py") `
    -- --expected-version $Version --report (Join-Path $ReportDir "environment_windows.json")

& $BlenderExe `
    --background `
    --factory-startup `
    --disable-autoexec `
    --python-exit-code 1 `
    --python (Join-Path $Root "blender_env\scripts\create_roblox_workspace.py") `
    -- (Join-Path $Root "artifacts\ROBLOX_CONTRACT_WORKSPACE_4_5.blend")

Write-Host "Ambiente Blender pronto em $InstallDir"
