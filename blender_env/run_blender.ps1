param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Script,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BlenderExe = Join-Path $Root ".tools\blender\4.5.12\blender.exe"

if (-not (Test-Path $BlenderExe)) {
    throw "Execute blender_env/bootstrap_windows.ps1 primeiro"
}

$ResolvedScript = (Resolve-Path $Script).Path
& $BlenderExe `
    --background `
    --factory-startup `
    --disable-autoexec `
    --python-exit-code 1 `
    --python $ResolvedScript `
    -- @ScriptArgs

exit $LASTEXITCODE
