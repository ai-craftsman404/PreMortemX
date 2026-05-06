[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$indexPath = Join-Path $pluginRoot "registry\\runs\\index.jsonl"
$qualityLogPath = Join-Path $pluginRoot "registry\\quality-review-log.json"
$viewsRoot = Join-Path $pluginRoot "registry\\views"
$latestByProjectPath = Join-Path $viewsRoot "latest-by-project.json"
$attentionQueuePath = Join-Path $viewsRoot "attention-queue.json"
$dashboardPath = Join-Path $viewsRoot "dashboard.md"

New-Item -ItemType Directory -Path $viewsRoot -Force | Out-Null

if (-not (Test-Path -LiteralPath $indexPath)) {
    @{} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $latestByProjectPath
    @() | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $attentionQueuePath
    @(
        "# PreMortemX Registry Dashboard"
        ""
        "- Total runs: 0"
        "- Attention queue: 0"
        ""
        "## Latest By Project"
        ""
        "- No runs recorded."
    ) | Set-Content -LiteralPath $dashboardPath

    [pscustomobject]@{
        totalRuns = 0
        projects = 0
        attention = 0
    } | ConvertTo-Json -Depth 4
    return
}

$items = @()
foreach ($line in Get-Content -LiteralPath $indexPath) {
    if (-not [string]::IsNullOrWhiteSpace($line)) {
        $items += ($line | ConvertFrom-Json)
    }
}

$sorted = @($items | Sort-Object createdAt -Descending)

$latestByProject = [ordered]@{}
foreach ($item in $sorted) {
    if (-not $latestByProject.Contains($item.projectSlug)) {
        $latestByProject[$item.projectSlug] = $item
    }
}

$reviewItems = @()
if (Test-Path -LiteralPath $qualityLogPath) {
    $qualityLog = Get-Content -LiteralPath $qualityLogPath -Raw | ConvertFrom-Json
    if ($null -ne $qualityLog.items) {
        $reviewItems = @($qualityLog.items)
    }
}

$reviewedRunIds = @{}
foreach ($review in $reviewItems) {
    $reviewedRunIds[$review.runId] = $review
}

$attentionQueue = @(
    $sorted | Where-Object {
        ($_.decision -eq "Block") -or
        ($_.overrideApplied -eq $true) -or
        (-not $reviewedRunIds.ContainsKey($_.runId))
    }
)

$latestByProject | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $latestByProjectPath
if ($attentionQueue.Count -eq 0) {
    "[]" | Set-Content -LiteralPath $attentionQueuePath
}
else {
    $attentionQueue | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $attentionQueuePath
}

$blockCount = @($sorted | Where-Object { $_.decision -eq "Block" }).Count
$overrideCount = @($sorted | Where-Object { $_.overrideApplied -eq $true }).Count
$reviewedCount = $reviewItems.Count
$pendingReviewCount = @($sorted | Where-Object { -not $reviewedRunIds.ContainsKey($_.runId) }).Count
$falsePositiveCount = @($reviewItems | Where-Object { $_.reviewOutcome -eq "false-positive" }).Count
$missedRiskCount = @($reviewItems | Where-Object { $_.reviewOutcome -eq "missed-risk" }).Count

$dashboard = @(
    "# PreMortemX Registry Dashboard"
    ""
    "- Total runs: $($sorted.Count)"
    "- Projects tracked: $($latestByProject.Count)"
    "- Blocks: $blockCount"
    "- Overrides: $overrideCount"
    "- Reviewed runs: $reviewedCount"
    "- Pending quality follow-up: $pendingReviewCount"
    "- False positives logged: $falsePositiveCount"
    "- Missed risks logged: $missedRiskCount"
    "- Attention queue: $($attentionQueue.Count)"
    ""
    "## Latest By Project"
    ""
)

if ($latestByProject.Count -eq 0) {
    $dashboard += "- No runs recorded."
}
else {
    foreach ($project in $latestByProject.Keys) {
        $entry = $latestByProject[$project]
        $dashboard += "- ${project}: $($entry.decision) [$($entry.mode)] at $($entry.createdAt)"
    }
}

$dashboard | Set-Content -LiteralPath $dashboardPath

[pscustomobject]@{
    totalRuns = $sorted.Count
    projects = $latestByProject.Count
    attention = $attentionQueue.Count
} | ConvertTo-Json -Depth 4
