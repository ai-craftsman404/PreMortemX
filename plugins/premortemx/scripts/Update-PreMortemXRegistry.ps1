[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RunRecordPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $RunRecordPath)) {
    throw "Run record not found: $RunRecordPath"
}

$record = Get-Content -LiteralPath $RunRecordPath -Raw | ConvertFrom-Json
$pluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$indexPath = Join-Path $pluginRoot "registry\\runs\\index.jsonl"
$qualityLogPath = Join-Path $pluginRoot "registry\\quality-review-log.json"

New-Item -ItemType Directory -Path (Split-Path -Parent $indexPath) -Force | Out-Null

$indexRecord = [ordered]@{
    runId = $record.runId
    createdAt = $record.createdAt
    updatedAt = $record.updatedAt
    projectSlug = $record.projectSlug
    mode = $record.mode
    taskCategory = $record.taskCategory
    decision = $record.decision
    confidenceBand = $record.confidenceBand
    artifactPath = $record.artifactPath
    likelySensitive = $record.sensitivityReview.likelySensitive
    overrideApplied = $record.override.applied
    promotionState = $record.calibrationState.promotionState
    deliberationStatus = $record.deliberation.status
}

Add-Content -LiteralPath $indexPath -Value ($indexRecord | ConvertTo-Json -Compress)

if (-not (Test-Path -LiteralPath $qualityLogPath)) {
    (@{
        items = @()
    } | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $qualityLogPath
}

$indexRecord | ConvertTo-Json -Depth 4
