# Sync RIGGWIRE v3.10 to all locations
$source = "C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO-LIVE"
$files = @("RIGGWIRE_FINAL.mq5", "StrategyManager.mqh", "PositionManagement.mqh", "TrendConfirmation.mqh")

Write-Host "`nSyncing RIGGWIRE v3.10 fixed files..." -ForegroundColor Cyan

# Project locations
$project_dirs = @(
    "C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO",
    "C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\WINDOWS_COMPILE_PACKAGE"
)

$count = 0
foreach ($dir in $project_dirs) {
    if (Test-Path $dir) {
        foreach ($file in $files) {
            Copy-Item "$source\$file" "$dir\$file" -Force
            $count++
        }
        Write-Host "  Project: $dir" -ForegroundColor Green
    }
}

# Terminal locations
$terminals = @("5C659F0E64BA794E712EE4C936BCFED5", "6DA6984F1D660957811E5E6B8FD78B02", "D0E8209F77C8CF37AD8BF550E51FF075", "F2262CFAFF47C27887389DAB2852351A", "F762D69EEEA9B4430D7F17C82167C844", "Common", "Community")
$base = "C:\Users\dorwi\AppData\Roaming\MetaQuotes\Terminal"

foreach ($term in $terminals) {
    $paths = @(
        "$base\$term\MQL5\Experts",
        "$base\$term\MQL5\Experts\RIGGWIRE-EA-FTMO",
        "$base\$term\MQL5\Experts\RIGGWIRE-EA-FTMO-LIVE",
        "$base\$term\MQL5\Experts\RIGGWIRE-EA-main",
        "$base\$term\MQL5\Experts\riggwire-ea-136",
        "$base\$term\MQL5\Indicators",
        "$base\$term\MQL5\Indicators\RIGGWIRE-EA-FTMO",
        "$base\$term\MQL5\Indicators\RIGGWIRE-EA-FTMO-LIVE"
    )

    foreach ($path in $paths) {
        if (Test-Path $path) {
            foreach ($file in $files) {
                $dest = "$path\$file"
                if (Test-Path $dest) {
                    Copy-Item "$source\$file" $dest -Force
                    $count++
                }
            }
        }
    }
}

Write-Host "`nTotal files synced: $count" -ForegroundColor Green
Write-Host "Version 3.10 deployed to all locations" -ForegroundColor Green
