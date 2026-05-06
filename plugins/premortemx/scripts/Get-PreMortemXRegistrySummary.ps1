[CmdletBinding()]
param(
    [string]$ProjectSlug,
    [ValidateSet("all", "release-risk-gating", "architecture-validation")]
    [string]$Mode = "all",
    [int]$Limit = 20
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$indexPath = Join-Path $pluginRoot "registry\\runs\\index.jsonl"
$qualityLogPath = Join-Path $pluginRoot "registry\\quality-review-log.json"

if (-not (Test-Path -LiteralPath $indexPath)) {
    [pscustomobject]@{
        totalRuns = 0
        byDecision = @{}
        byMode = @{}
        totalReviewed = 0
        pendingQualityFollowup = 0
        byReviewOutcome = @{}
        latestRuns = @()
    } | ConvertTo-Json -Depth 8
    return
}

$items = @()
foreach ($line in Get-Content -LiteralPath $indexPath) {
    if (-not [string]::IsNullOrWhiteSpace($line)) {
        $items += ($line | ConvertFrom-Json)
    }
}

if ($ProjectSlug) {
    $items = @($items | Where-Object { $_.projectSlug -eq $ProjectSlug })
}

if ($Mode -ne "all") {
    $items = @($items | Where-Object { $_.mode -eq $Mode })
}

$sorted = @($items | Sort-Object createdAt -Descending)
$latest = @($sorted | Select-Object -First $Limit)

$decisionGroups = @{}
foreach ($group in ($items | Group-Object decision)) {
    $decisionGroups[$group.Name] = $group.Count
}

$modeGroups = @{}
foreach ($group in ($items | Group-Object mode)) {
    $modeGroups[$group.Name] = $group.Count
}

$reviewItems = @()
if (Test-Path -LiteralPath $qualityLogPath) {
    $qualityLog = Get-Content -LiteralPath $qualityLogPath -Raw | ConvertFrom-Json
    if ($null -ne $qualityLog.items) {
        $reviewItems = @($qualityLog.items)
    }
}

if ($ProjectSlug) {
    $reviewItems = @($reviewItems | Where-Object { $_.projectSlug -eq $ProjectSlug })
}

if ($Mode -ne "all") {
    $reviewItems = @($reviewItems | Where-Object { $_.mode -eq $Mode })
}

$reviewOutcomeGroups = @{}
foreach ($group in ($reviewItems | Group-Object reviewOutcome)) {
    $reviewOutcomeGroups[$group.Name] = $group.Count
}

$reviewedRunIds = @{}
foreach ($review in $reviewItems) {
    $reviewedRunIds[$review.runId] = $true
}

$pendingQualityFollowup = @($items | Where-Object { -not $reviewedRunIds.ContainsKey($_.runId) }).Count

[pscustomobject]@{
    totalRuns = $items.Count
    byDecision = $decisionGroups
    byMode = $modeGroups
    totalReviewed = $reviewItems.Count
    pendingQualityFollowup = $pendingQualityFollowup
    byReviewOutcome = $reviewOutcomeGroups
    latestRuns = $latest
} | ConvertTo-Json -Depth 8
