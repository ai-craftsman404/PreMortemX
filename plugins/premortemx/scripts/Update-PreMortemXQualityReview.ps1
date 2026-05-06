[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RunRecordPath,

    [ValidateSet("accurate", "false-positive", "missed-risk", "mixed", "unknown")]
    [string]$ReviewOutcome = "unknown",

    [string]$Reviewer = "codex",

    [string]$OutcomeNotes,

    [string]$FalsePositiveNotes,

    [string]$MissedRiskNotes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $RunRecordPath)) {
    throw "Run record not found: $RunRecordPath"
}

$pluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$qualityLogPath = Join-Path $pluginRoot "registry\\quality-review-log.json"

$record = Get-Content -LiteralPath $RunRecordPath -Raw | ConvertFrom-Json

if (-not (Test-Path -LiteralPath $qualityLogPath)) {
    (@{ items = @() } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $qualityLogPath
}

$log = Get-Content -LiteralPath $qualityLogPath -Raw | ConvertFrom-Json
$items = @()
if ($null -ne $log.items) {
    $items = @($log.items)
}

$existing = $items | Where-Object { $_.runId -eq $record.runId } | Select-Object -First 1
$reviewedAt = (Get-Date).ToUniversalTime().ToString("o")

if ($null -eq $existing) {
    $review = [pscustomobject]@{
        runId = $record.runId
        projectSlug = $record.projectSlug
        mode = $record.mode
        taskCategory = $record.taskCategory
        decision = $record.decision
        reviewOutcome = $ReviewOutcome
        reviewer = $Reviewer
        reviewedAt = $reviewedAt
        outcomeNotes = @()
        falsePositiveNotes = @()
        missedRiskNotes = @()
    }
    $items += $review
    $existing = $review
}
else {
    $existing.reviewOutcome = $ReviewOutcome
    $existing.reviewer = $Reviewer
    $existing.reviewedAt = $reviewedAt
}

if ($OutcomeNotes) {
    $existing.outcomeNotes = @($existing.outcomeNotes) + $OutcomeNotes
}
if ($FalsePositiveNotes) {
    $existing.falsePositiveNotes = @($existing.falsePositiveNotes) + $FalsePositiveNotes
}
if ($MissedRiskNotes) {
    $existing.missedRiskNotes = @($existing.missedRiskNotes) + $MissedRiskNotes
}

[pscustomobject]@{
    items = $items
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $qualityLogPath

$record.qualityFollowup.status = "reviewed"
$record.qualityFollowup.outcomeNotes = @($record.qualityFollowup.outcomeNotes) + @($existing.outcomeNotes)
$record.qualityFollowup.falsePositiveNotes = @($record.qualityFollowup.falsePositiveNotes) + @($existing.falsePositiveNotes)
$record.qualityFollowup.missedRiskNotes = @($record.qualityFollowup.missedRiskNotes) + @($existing.missedRiskNotes)
$record.updatedAt = $reviewedAt
$record | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $RunRecordPath

$existing | ConvertTo-Json -Depth 8
