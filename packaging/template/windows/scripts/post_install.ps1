param(
    [Parameter(Mandatory = $true)]
    [string]$AppDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PythonBootstrapCommand {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @('py', '-3')
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @('python')
    }

    throw "Python 3 not found. Install Python and ensure 'py' or 'python' is available in PATH."
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Command,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    Write-Host "[INFO] $Description"
    Write-Host "[CMD ] $($Command -join ' ')"

    & $Command[0] $Command[1..($Command.Length - 1)]
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $($Command -join ' ')"
    }
}

$venvRoot = Join-Path $env:LOCALAPPDATA 'SmartOdoo'
$venvDir = Join-Path $venvRoot 'venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
$requirements = Join-Path $AppDir 'requirements.txt'

if (-not (Test-Path -LiteralPath $requirements)) {
    throw "requirements.txt not found in $AppDir"
}

New-Item -ItemType Directory -Path $venvRoot -Force | Out-Null

if (-not (Test-Path -LiteralPath $venvPython)) {
    $bootstrap = Get-PythonBootstrapCommand
    Invoke-Checked -Command ($bootstrap + @('-m', 'venv', $venvDir)) -Description 'Creating virtual environment'
}

Invoke-Checked -Command @($venvPython, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel') -Description 'Updating pip tooling'
Invoke-Checked -Command @($venvPython, '-m', 'pip', 'install', '-r', $requirements) -Description 'Installing SmartOdoo dependencies'

$markerPath = Join-Path $venvRoot 'installed_by_inno.txt'
@(
    "installed_at=$(Get-Date -Format o)",
    "app_dir=$AppDir"
) | Set-Content -LiteralPath $markerPath -Encoding UTF8

Write-Host '[OK] SmartOdoo environment prepared successfully.'
