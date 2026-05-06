[CmdletBinding()]
param(
    [string]$ProjectSlug,
    [ValidateSet("all", "release-risk-gating", "architecture-validation")]
    [string]$Mode = "all"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$qualityLogPath = Join-Path $pluginRoot "registry\\quality-review-log.json"

if (-not (Test-Path -LiteralPath $qualityLogPath)) {
    [pscustomobject]@{
        totalReviewed = 0
        byOutcome = @{}
        byMode = @{}
        latestReviews = @()
    } | ConvertTo-Json -Depth 8
    return
}

$log = Get-Content -LiteralPath $qualityLogPath -Raw | ConvertFrom-Json
$items = @()
if ($null -ne $log.items) {
    $items = @($log.items)
}

if ($ProjectSlug) {
    $items = @($items | Where-Object { $_.projectSlug -eq $ProjectSlug })
}

if ($Mode -ne "all") {
    $items = @($items | Where-Object { $_.mode -eq $Mode })
}

$outcomeGroups = @{}
foreach ($group in ($items | Group-Object reviewOutcome)) {
    $outcomeGroups[$group.Name] = $group.Count
}

$modeGroups = @{}
foreach ($group in ($items | Group-Object mode)) {
    $modeGroups[$group.Name] = $group.Count
}

[pscustomobject]@{
    totalReviewed = $items.Count
    byOutcome = $outcomeGroups
    byMode = $modeGroups
    latestReviews = @($items | Sort-Object reviewedAt -Descending | Select-Object -First 20)
} | ConvertTo-Json -Depth 8
