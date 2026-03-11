# ============================================================
# BOILERPLATE TEAMWORK - Klonowanie orkiestracji agentow
# Wersja: 3.0.1 | Data: 2026-03-05
# ============================================================
param(
    [Parameter(Mandatory=$true)]
    [string]$TargetPath,

    [Parameter(Mandatory=$false)]
    [string]$ProjectName = ""
)

$ErrorActionPreference = "Stop"
$SourcePath = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host " BOILERPLATE TEAMWORK - Klonowanie zespolu" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Zrodlo:  $SourcePath" -ForegroundColor Gray
Write-Host "  Cel:     $TargetPath" -ForegroundColor Gray
if ($ProjectName) { Write-Host "  Projekt: $ProjectName" -ForegroundColor Gray }
Write-Host ""

if (-not (Test-Path $SourcePath)) {
    Write-Host "[ERROR] Nie znaleziono zrodla: $SourcePath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "$SourcePath\.agents\TEAM_RULES.md")) {
    Write-Host "[ERROR] Brak TEAM_RULES.md w zrodle." -ForegroundColor Red
    exit 1
}

Write-Host "Tworzenie struktury katalogow..." -ForegroundColor Yellow
$dirs = @(
    "$TargetPath\.agents\workflows",
    "$TargetPath\TeamEngine\scripts",
    "$TargetPath\docs\blueprint\tom1-wiedza",
    "$TargetPath\docs\blueprint\tom2-technologia",
    "$TargetPath\docs\blueprint\tom3-specyfikacja",
    "$TargetPath\docs\blueprint\tom4-skills",
    "$TargetPath\docs\blueprint\tom5-research",
    "$TargetPath\docs\sprints"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host "Kopiowanie agentow..." -ForegroundColor Yellow
Copy-Item "$SourcePath\.agents\TEAM_RULES.md" "$TargetPath\.agents\TEAM_RULES.md" -Force
$workflows = Get-ChildItem "$SourcePath\.agents\workflows\*.md"
foreach ($wf in $workflows) {
    Copy-Item $wf.FullName "$TargetPath\.agents\workflows\$($wf.Name)" -Force
}
Copy-Item "$SourcePath\TeamEngine\scripts\deploy_engine.ps1" "$TargetPath\TeamEngine\scripts\deploy_engine.ps1" -Force
Copy-Item "$SourcePath\TeamEngine\scripts\update_engine.ps1" "$TargetPath\TeamEngine\scripts\update_engine.ps1" -Force
Copy-Item "$SourcePath\TeamEngine\README.md" "$TargetPath\TeamEngine\README.md" -Force

Write-Host "Kopiowanie szablonow Blueprint..." -ForegroundColor Yellow
Copy-Item "$SourcePath\docs\blueprint\00_master_knowledge_map.md" "$TargetPath\docs\blueprint\00_master_knowledge_map.md" -Force

$templateFiles = @(
    @{ src = "docs\blueprint\tom3-specyfikacja\01_inbox_pomysly.md"; dst = "docs\blueprint\tom3-specyfikacja\01_inbox_pomysly.md" },
    @{ src = "docs\blueprint\tom3-specyfikacja\02_roadmap.md"; dst = "docs\blueprint\tom3-specyfikacja\02_roadmap.md" },
    @{ src = "docs\blueprint\tom4-skills\06_sprint_artifact_template.md"; dst = "docs\blueprint\tom4-skills\06_sprint_artifact_template.md" },
    @{ src = "docs\blueprint\tom4-skills\07_team_engine.md"; dst = "docs\blueprint\tom4-skills\07_team_engine.md" }
)

foreach ($tf in $templateFiles) {
    $srcFull = Join-Path $SourcePath $tf.src
    $dstFull = Join-Path $TargetPath $tf.dst
    if (Test-Path $srcFull) {
        Copy-Item $srcFull $dstFull -Force
    }
}

# Error Registry — pusty szablon
$errRegSrc = Join-Path $SourcePath "docs\blueprint\tom1-wiedza\error_registry.md"
$errRegDst = Join-Path $TargetPath "docs\blueprint\tom1-wiedza\error_registry.md"
if (Test-Path $errRegSrc) {
    Copy-Item $errRegSrc $errRegDst -Force
}

Write-Host "Reset tresci projektowej..." -ForegroundColor Yellow
$inboxPath = "$TargetPath\docs\blueprint\tom3-specyfikacja\01_inbox_pomysly.md"
$projNameStr = if ($ProjectName) { $ProjectName } else { "Nowy Projekt" }
$inboxContent = "# INBOX - $projNameStr`n> TU WRZUCAJ LUZNE MYSLI I ZADANIA!`n`n## Nowe Sprawy`n- [ ] ...`n`n## Posortowane`n"
Set-Content -Path $inboxPath -Value $inboxContent -Encoding UTF8

if ($ProjectName) {
    Write-Host "Aktualizacja nazwy projektu..." -ForegroundColor Yellow
    $mapPath = "$TargetPath\docs\blueprint\00_master_knowledge_map.md"
    $mapContent = Get-Content $mapPath -Raw -Encoding UTF8
    $mapContent = $mapContent -replace "PM Center", $ProjectName
    $mapContent = $mapContent -replace "PM_Center", $ProjectName
    Set-Content -Path $mapPath -Value $mapContent -Encoding UTF8

    $rulesPath = "$TargetPath\.agents\TEAM_RULES.md"
    $rulesContent = Get-Content $rulesPath -Raw -Encoding UTF8
    $rulesContent = $rulesContent -replace "PM_CENTER", $ProjectName.ToUpper()
    $rulesContent = $rulesContent -replace "PM_Center", $ProjectName
    Set-Content -Path $rulesPath -Value $rulesContent -Encoding UTF8

    $pmPath = "$TargetPath\.agents\workflows\pm.md"
    $pmContent = Get-Content $pmPath -Raw -Encoding UTF8
    $pmContent = $pmContent -replace "PM_Center", $ProjectName
    Set-Content -Path $pmPath -Value $pmContent -Encoding UTF8
}

Write-Host "GOTOWE!" -ForegroundColor Green
