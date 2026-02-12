# Sync RIGGWIRE v3.10 Fixed Files to All Locations
# Date: 2026-02-07
# Fixes Applied: 22 (5 Critical, 8 High, 7 Medium, 2 Low)

$ErrorActionPreference = "Continue"
$source_dir = "C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO-LIVE"

# Files to sync
$files = @(
    "RIGGWIRE_FINAL.mq5",
    "StrategyManager.mqh",
    "PositionManagement.mqh",
    "TrendConfirmation.mqh"
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RIGGWIRE v3.10 - File Sync Script" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Verify source files exist
$missing_files = @()
foreach ($file in $files) {
    $source_path = Join-Path $source_dir $file
    if (-not (Test-Path $source_path)) {
        $missing_files += $file
    }
}

if ($missing_files.Count -gt 0) {
    Write-Host "ERROR: Source files not found:" -ForegroundColor Red
    $missing_files | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "Source Directory: $source_dir" -ForegroundColor Green
Write-Host "Files to Sync:" -ForegroundColor Green
$files | ForEach-Object { Write-Host "  ✓ $_" -ForegroundColor Green }
Write-Host ""

# PROJECT LOCATIONS
Write-Host "=== PROJECT LOCATIONS ===" -ForegroundColor Yellow
$project_destinations = @(
    "C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO",
    "C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\WINDOWS_COMPILE_PACKAGE"
)

$project_count = 0
foreach ($dest_dir in $project_destinations) {
    if (Test-Path $dest_dir) {
        foreach ($file in $files) {
            $source_file = Join-Path $source_dir $file
            $dest_file = Join-Path $dest_dir $file

            try {
                Copy-Item -Path $source_file -Destination $dest_file -Force
                Write-Host "  ✓ $dest_dir\$file" -ForegroundColor Green
                $project_count++
            } catch {
                Write-Host "  ✗ FAILED: $dest_dir\$file - $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}

# TERMINAL LOCATIONS
Write-Host "`n=== TERMINAL LOCATIONS ===" -ForegroundColor Yellow

$terminal_base = "C:\Users\dorwi\AppData\Roaming\MetaQuotes\Terminal"
$terminal_ids = @(
    "5C659F0E64BA794E712EE4C936BCFED5",
    "6DA6984F1D660957811E5E6B8FD78B02",
    "D0E8209F77C8CF37AD8BF550E51FF075",
    "F2262CFAFF47C27887389DAB2852351A",
    "F762D69EEEA9B4430D7F17C82167C844",
    "Common",
    "Community"
)

$terminal_subdirs = @(
    "MQL5\Experts",
    "MQL5\Experts\RIGGWIRE-EA-FTMO",
    "MQL5\Experts\RIGGWIRE-EA-FTMO-LIVE",
    "MQL5\Experts\RIGGWIRE-EA-main",
    "MQL5\Experts\riggwire-ea-136",
    "MQL5\Indicators",
    "MQL5\Indicators\RIGGWIRE-EA-FTMO",
    "MQL5\Indicators\RIGGWIRE-EA-FTMO-LIVE"
)

$terminal_count = 0
foreach ($terminal_id in $terminal_ids) {
    $terminal_path = Join-Path $terminal_base $terminal_id

    if (Test-Path $terminal_path) {
        Write-Host "`nTerminal: $terminal_id" -ForegroundColor Cyan

        foreach ($subdir in $terminal_subdirs) {
            $dest_dir = Join-Path $terminal_path $subdir

            if (Test-Path $dest_dir) {
                foreach ($file in $files) {
                    $source_file = Join-Path $source_dir $file
                    $dest_file = Join-Path $dest_dir $file

                    # Only copy if destination file exists (don't create new locations)
                    if (Test-Path $dest_file) {
                        try {
                            Copy-Item -Path $source_file -Destination $dest_file -Force
                            Write-Host "  ✓ $subdir\$file" -ForegroundColor Green
                            $terminal_count++
                        } catch {
                            Write-Host "  ✗ FAILED: $subdir\$file - $($_.Exception.Message)" -ForegroundColor Red
                        }
                    }
                }
            }
        }
    }
}

# SUMMARY
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SYNC COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project Files Synced:  $project_count" -ForegroundColor Green
Write-Host "Terminal Files Synced: $terminal_count" -ForegroundColor Green
Write-Host "Total Files Synced:    $($project_count + $terminal_count)" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Recompile in MetaEditor (F7)" -ForegroundColor White
Write-Host "2. Verify version shows 3.10" -ForegroundColor White
Write-Host "3. Run backtest to validate fixes" -ForegroundColor White
Write-Host "4. Deploy to demo for 24h observation" -ForegroundColor White
Write-Host ""
