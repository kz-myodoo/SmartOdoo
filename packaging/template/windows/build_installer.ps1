param(
    [string]$Version = '',
    [string]$IsccPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$packagingDir = Split-Path -Parent (Split-Path -Parent $scriptRoot)
$projectRoot = Split-Path -Parent $packagingDir
$buildDir = Join-Path $packagingDir 'build'
$sourceConfigPath = Join-Path $projectRoot 'config\config.json'
$windowsConfigPath = Join-Path $buildDir 'config.windows.json'
$issPath = Join-Path $scriptRoot 'installer\SmartOdoo.iss'

if (-not (Test-Path -LiteralPath $issPath)) {
    throw "Inno Setup script not found: $issPath"
}

if (-not (Test-Path -LiteralPath $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
}

if (-not (Test-Path -LiteralPath $sourceConfigPath)) {
    throw "Config file not found: $sourceConfigPath"
}

$configData = Get-Content -LiteralPath $sourceConfigPath -Raw | ConvertFrom-Json
$null = $configData.PSObject.Properties.Remove('linux')
$configJson = $configData | ConvertTo-Json -Depth 20
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($windowsConfigPath, $configJson + [Environment]::NewLine, $utf8NoBom)

function Resolve-PackageVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RootDir
    )

    $pythonCandidates = @('python', 'py')
    foreach ($candidate in $pythonCandidates) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $cmd) {
            continue
        }

        $script = @"
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
from app.core.version import get_smartodoo_version

print(get_smartodoo_version(root_dir=root))
"@

        if ($candidate -eq 'py') {
            $resolved = & $cmd.Source -3 -c $script $RootDir 2>$null
        } else {
            $resolved = & $cmd.Source -c $script $RootDir 2>$null
        }

        if ($LASTEXITCODE -eq 0 -and $resolved) {
            $version = ($resolved | Select-Object -First 1).Trim()
            if ($version) {
                return $version
            }
        }
    }

    throw "Could not resolve package version from app/core/version.py. Install Python and ensure 'python' or 'py' is available in PATH."
}

$resolvedVersion = $Version
if (-not $resolvedVersion) {
    $resolvedVersion = Resolve-PackageVersion -RootDir $projectRoot
}

if ($resolvedVersion -eq 'dev') {
    throw "Resolved package version is 'dev'; set a release version in app/setup.py"
}

$possibleIscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)

$iscc = ''

if ($IsccPath) {
    if (-not (Test-Path -LiteralPath $IsccPath)) {
        throw "Provided -IsccPath does not exist: $IsccPath"
    }
    $iscc = $IsccPath
} else {
    $iscc = $possibleIscc | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $iscc) {
        $isccCmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
        if ($isccCmd) {
            $iscc = $isccCmd.Source
        }
    }
}

if (-not $iscc) {
    $searchedPaths = ($possibleIscc -join '; ')
    throw "ISCC.exe not found. Install Inno Setup 6: https://jrsoftware.org/isdl.php`nSearched: $searchedPaths`nYou can also run with -IsccPath 'C:\path\to\ISCC.exe'."
}

Write-Host "[INFO] Building SmartOdoo installer version $resolvedVersion"
& $iscc "/DMyAppVersion=$resolvedVersion" "/DMySourceRoot=$projectRoot" "/DMyOutputDir=$buildDir" "/DMyConfigJsonPath=$windowsConfigPath" "$issPath"
if ($LASTEXITCODE -ne 0) {
    throw "ISCC failed with exit code $LASTEXITCODE"
}

Write-Host "[OK] Installer build finished. Output directory: $buildDir"
