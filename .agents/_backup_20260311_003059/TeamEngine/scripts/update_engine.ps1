# ============================================================
# ð UPDATE TEAMWORK â Aktualizacja orkiestracji z zachowaniem skilli
# Wersja: 3.0.1 | Data: 2026-03-05
# ============================================================
# UÅ¼ycie:
#   .\update_engine.ps1 -SourcePath "C:\od_zera_do_ai\PM_Center" -TargetPath "C:\inny_projekt"
#   .\update_engine.ps1 -SourcePath "C:\od_zera_do_ai\PM_Center" -TargetPath "C:\inny_projekt" -DryRun
#
# Co robi:
#   1. Aktualizuje CORE (TEAM_RULES, workflows, skrypty)
#   2. NIE rusza PROJECT (PROJECT_SKILLS, docs/blueprint treÅÄ, sprints)
#   3. Pokazuje diff wersji przed i po
#   4. Tworzy backup plikÃ³w przed nadpisaniem
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$SourcePath,

    [Parameter(Mandatory=$true)]
    [string]$TargetPath,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " ð UPDATE TEAMWORK â Bezpieczna aktualizacja" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Å¹rÃ³dÅo (master):  $SourcePath" -ForegroundColor Gray
Write-Host "  Cel (projekt):    $TargetPath" -ForegroundColor Gray
if ($DryRun) {
    Write-Host "  â ï¸  TRYB DRY RUN â nic nie zostanie zmienione" -ForegroundColor Yellow
}
Write-Host ""

# --- WALIDACJA ---
if (-not (Test-Path "$SourcePath\.agents\TEAM_RULES.md")) {
    Write-Host "â BÅÄD: Brak TEAM_RULES.md w ÅºrÃ³dle: $SourcePath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "$TargetPath\.agents")) {
    Write-Host "â BÅÄD: Brak .agents/ w celu: $TargetPath â uÅ¼yj deploy_engine.ps1 zamiast update" -ForegroundColor Red
    exit 1
}

# --- PORÃWNANIE WERSJI ---
Write-Host "ð PorÃ³wnanie wersji..." -ForegroundColor Yellow

$srcVersion = "nieznana"
$dstVersion = "nieznana"

$srcRules = Get-Content "$SourcePath\.agents\TEAM_RULES.md" -Raw -Encoding UTF8
if ($srcRules -match 'Wersja:\*\*\s*([0-9.]+)') { $srcVersion = $Matches[1] }

if (Test-Path "$TargetPath\.agents\TEAM_RULES.md") {
    $dstRules = Get-Content "$TargetPath\.agents\TEAM_RULES.md" -Raw -Encoding UTF8
    if ($dstRules -match 'Wersja:\*\*\s*([0-9.]+)') { $dstVersion = $Matches[1] }
}

Write-Host "  Å¹rÃ³dÅo: v$srcVersion" -ForegroundColor White
Write-Host "  Cel:    v$dstVersion" -ForegroundColor White

if ($srcVersion -eq $dstVersion) {
    Write-Host ""
    Write-Host "â Wersje identyczne â brak potrzeby aktualizacji." -ForegroundColor Green
    exit 0
}

Write-Host "  â Aktualizacja: v$dstVersion â v$srcVersion" -ForegroundColor Cyan
Write-Host ""

# --- DEFINICJA WARSTW ---

# ð¢ CORE â bezpiecznie nadpisywane
$coreFiles = @(
    @{ rel = ".agents\TEAM_RULES.md" },
    @{ rel = ".agents\workflows\pm.md" },
    @{ rel = ".agents\workflows\arch.md" },
    @{ rel = ".agents\workflows\dev.md" },
    @{ rel = ".agents\workflows\dev_worker.md" },
    @{ rel = ".agents\workflows\qa.md" },
    @{ rel = ".agents\workflows\sec.md" },
    @{ rel = ".agents\workflows\anal.md" },
    @{ rel = "TeamEngine\scripts\deploy_engine.ps1" },
    @{ rel = "TeamEngine\scripts\update_engine.ps1" },
    @{ rel = "TeamEngine\README.md" },
    @{ rel = "docs\blueprint\tom4-skills\06_sprint_artifact_template.md" },
    @{ rel = "docs\blueprint\tom4-skills\07_team_engine.md" }
)

# ð´ PROTECTED â NIGDY nie nadpisywane
$protectedFiles = @(
    ".agents\PROJECT_SKILLS.md",
    "docs\blueprint\00_master_knowledge_map.md",
    "docs\blueprint\tom1-wiedza\*",
    "docs\blueprint\tom2-technologia\*",
    "docs\blueprint\tom3-specyfikacja\*",
    "docs\blueprint\tom4-skills\*",
    "docs\blueprint\tom5-research\*",
    "docs\sprints\*"
)

# --- BACKUP ---
$backupDir = "$TargetPath\.agents\_backup_$timestamp"

if (-not $DryRun) {
    Write-Host "ð¾ Tworzenie backupu..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

    foreach ($cf in $coreFiles) {
        $targetFile = Join-Path $TargetPath $cf.rel
        if (Test-Path $targetFile) {
            $backupFile = Join-Path $backupDir $cf.rel
            $backupFileDir = Split-Path $backupFile -Parent
            if (-not (Test-Path $backupFileDir)) {
                New-Item -ItemType Directory -Path $backupFileDir -Force | Out-Null
            }
            Copy-Item $targetFile $backupFile -Force
        }
    }
    Write-Host "  â Backup w: $backupDir" -ForegroundColor Green
}

# --- AKTUALIZACJA CORE ---
Write-Host ""
Write-Host "ð Aktualizacja plikÃ³w CORE..." -ForegroundColor Yellow

$updated = 0
$skipped = 0

foreach ($cf in $coreFiles) {
    $srcFile = Join-Path $SourcePath $cf.rel
    $dstFile = Join-Path $TargetPath $cf.rel

    if (-not (Test-Path $srcFile)) {
        Write-Host "  â ï¸  Brak w ÅºrÃ³dle: $($cf.rel)" -ForegroundColor Yellow
        $skipped++
        continue
    }

    if ($DryRun) {
        if (Test-Path $dstFile) {
            $srcHash = (Get-FileHash $srcFile).Hash
            $dstHash = (Get-FileHash $dstFile).Hash
            if ($srcHash -ne $dstHash) {
                Write-Host "  ð ZMIENIONY: $($cf.rel)" -ForegroundColor Cyan
                $updated++
            } else {
                Write-Host "  â BEZ ZMIAN: $($cf.rel)" -ForegroundColor Gray
            }
        } else {
            Write-Host "  â NOWY: $($cf.rel)" -ForegroundColor Green
            $updated++
        }
    } else {
        $dstDir = Split-Path $dstFile -Parent
        if (-not (Test-Path $dstDir)) {
            New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
        }
        Copy-Item $srcFile $dstFile -Force
        Write-Host "  â $($cf.rel)" -ForegroundColor Green
        $updated++
    }
}

# --- WERYFIKACJA PROTECTED ---
Write-Host ""
Write-Host "ð¡ï¸  Pliki CHRONIONE (nienaruszone):" -ForegroundColor Yellow

foreach ($pf in $protectedFiles) {
    $fullPath = Join-Path $TargetPath $pf
    if (Test-Path $fullPath) {
        Write-Host "  ð $pf" -ForegroundColor Gray
    }
}

# Specjalnie sprawdÅº PROJECT_SKILLS.md
$skillsFile = "$TargetPath\.agents\PROJECT_SKILLS.md"
if (Test-Path $skillsFile) {
    Write-Host "  ð PROJECT_SKILLS.md â NIETKNIÄTY â" -ForegroundColor Green
} else {
    Write-Host "  â ï¸  PROJECT_SKILLS.md nie istnieje â kopiujÄ domyÅlny" -ForegroundColor Yellow
    if (-not $DryRun) {
        $srcSkills = "$SourcePath\.agents\PROJECT_SKILLS.md"
        if (Test-Path $srcSkills) {
            Copy-Item $srcSkills $skillsFile -Force
            Write-Host "  â Skopiowano domyÅlny PROJECT_SKILLS.md" -ForegroundColor Green
        }
    }
}

# --- PODSUMOWANIE ---
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
if ($DryRun) {
    Write-Host " ð DRY RUN COMPLETE" -ForegroundColor Yellow
} else {
    Write-Host " â UPDATE TEAM ENGINE â GOTOWE!" -ForegroundColor Green
}
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host " Wersja: v$dstVersion â v$srcVersion" -ForegroundColor White
Write-Host " Pliki CORE zaktualizowane: $updated" -ForegroundColor White
Write-Host " Pliki CHRONIONE (nietkniÄte): PROJECT_SKILLS.md + docs/" -ForegroundColor White
if (-not $DryRun) {
    Write-Host " Backup: $backupDir" -ForegroundColor White
}
Write-Host ""
Write-Host " ð§¹ Aby cofnÄÄ update:" -ForegroundColor Gray
Write-Host "    PrzywrÃ³Ä pliki z $backupDir" -ForegroundColor Gray
Write-Host ""
