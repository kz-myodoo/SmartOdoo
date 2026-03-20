Set-StrictMode -Version Latest
$ErrorActionPreference = 'SilentlyContinue'

$venvRoot = Join-Path $env:LOCALAPPDATA 'SmartOdoo'

if (Test-Path -LiteralPath $venvRoot) {
    Remove-Item -LiteralPath $venvRoot -Recurse -Force
}
