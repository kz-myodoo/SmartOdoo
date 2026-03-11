# ============================================================
# UPDATE TEAMWORK - TeamEngine Update Script
# Wersja: 3.2 | Data: 2026-03-11
# ============================================================
# Usage:
#   .\update_engine.ps1 -SourcePath "C:\od_zera_do_ai\PM_Center" -TargetPath "C:\other_project"
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
Write-Host " UPDATE TEAMWORK - Safe Update Engine" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Source:  $SourcePath" -ForegroundColor Gray
Write-Host "  Target:  $TargetPath" -ForegroundColor Gray
if ($DryRun) {
    Write-Host "  WARNING: DRY RUN MODE - no changes will be made" -ForegroundColor Yellow
}
Write-Host ""

# --- VALIDATION ---
if (-not (Test-Path "$SourcePath\.agents\TEAM_RULES.md")) {
    Write-Host "ERROR: Missing TEAM_RULES.md in source: $SourcePath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "$TargetPath\.agents")) {
    Write-Host "ERROR: Missing .agents/ in target: $TargetPath" -ForegroundColor Red
    exit 1
}

# --- VERSION COMPARISON ---
Write-Host "Comparing versions..." -ForegroundColor Yellow

$srcVersion = "unknown"
$dstVersion = "unknown"

$srcRules = Get-Content "$SourcePath\.agents\TEAM_RULES.md" -Raw -Encoding UTF8
if ($srcRules -match 'Wersja:\s*\*\*?\s*([0-9.]+)') { $srcVersion = $Matches[1] }

if (Test-Path "$TargetPath\.agents\TEAM_RULES.md") {
    $dstRules = Get-Content "$TargetPath\.agents\TEAM_RULES.md" -Raw -Encoding UTF8
    if ($dstRules -match 'Wersja:\s*\*\*?\s*([0-9.]+)') { $dstVersion = $Matches[1] }
}

Write-Host "  Source: v$srcVersion" -ForegroundColor White
Write-Host "  Target: v$dstVersion" -ForegroundColor White

if ($srcVersion -eq $dstVersion) {
    Write-Host ""
    Write-Host "Versions are identical - no update needed." -ForegroundColor Green
    exit 0
}

Write-Host "  -> Updating: v$dstVersion -> v$srcVersion" -ForegroundColor Cyan
Write-Host ""

# --- LAYERS DEFINITION ---
$coreFiles = @(
    @{ rel = ".agents\TEAM_RULES.md" },
    @{ rel = ".agents\workflows\pm.md" },
    @{ rel = ".agents\workflows\arch.md" },
    @{ rel = ".agents\workflows\dev.md" },
    @{ rel = ".agents\workflows\dev_worker.md" },
    @{ rel = ".agents\workflows\qa.md" },
    @{ rel = ".agents\workflows\audyt.md" },
    @{ rel = ".agents\workflows\sec.md" },
    @{ rel = ".agents\workflows\anal.md" },
    @{ rel = "TeamEngine\scripts\deploy_engine.ps1" },
    @{ rel = "TeamEngine\scripts\update_engine.ps1" },
    @{ rel = "TeamEngine\README.md" },
    @{ rel = "docs\blueprint\tom4-skills\06_sprint_artifact_template.md" },
    @{ rel = "docs\blueprint\tom4-skills\07_team_engine.md" }
)

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
    Write-Host "Creating backup..." -ForegroundColor Yellow
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
    Write-Host "  Backup created in: $backupDir" -ForegroundColor Green
}

# --- UPDATE CORE ---
Write-Host ""
Write-Host "Updating CORE files..." -ForegroundColor Yellow

$updated = 0
$skipped = 0

foreach ($cf in $coreFiles) {
    $srcFile = Join-Path $SourcePath $cf.rel
    $dstFile = Join-Path $TargetPath $cf.rel

    if (-not (Test-Path $srcFile)) {
        Write-Host "  Missing in source: $($cf.rel)" -ForegroundColor Yellow
        $skipped++
        continue
    }

    if ($DryRun) {
        if (Test-Path $dstFile) {
            $srcHash = (Get-FileHash $srcFile).Hash
            $dstHash = (Get-FileHash $dstFile).Hash
            if ($srcHash -ne $dstHash) {
                Write-Host "  CHANGED: $($cf.rel)" -ForegroundColor Cyan
                $updated++
            } else {
                Write-Host "  NO CHANGE: $($cf.rel)" -ForegroundColor Gray
            }
        } else {
            Write-Host "  NEW: $($cf.rel)" -ForegroundColor Green
            $updated++
        }
    } else {
        $dstDir = Split-Path $dstFile -Parent
        if (-not (Test-Path $dstDir)) {
            New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
        }
        Copy-Item $srcFile $dstFile -Force
        Write-Host "  Updated: $($cf.rel)" -ForegroundColor Green
        $updated++
    }
}

# --- SUMMARY ---
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
if ($DryRun) {
    Write-Host " DRY RUN COMPLETE" -ForegroundColor Yellow
} else {
    Write-Host " UPDATE TEAM ENGINE - DONE!" -ForegroundColor Green
}
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host " Version: v$dstVersion -> v$srcVersion" -ForegroundColor White
Write-Host " CORE files updated: $updated" -ForegroundColor White
if (-not $DryRun) {
    Write-Host " Backup: $backupDir" -ForegroundColor White
}
Write-Host ""
