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

function Test-HasProperty {
    param(
        [object]$Object,
        [string]$Name
    )

    return $null -ne $Object.PSObject.Properties[$Name]
}

$requiredTopLevel = @(
    "schemaVersion",
    "runId",
    "pluginVersion",
    "createdAt",
    "updatedAt",
    "status",
    "projectSlug",
    "taskType",
    "taskCategory",
    "executionMode",
    "approvalMode",
    "privacyMode",
    "retentionClass",
    "artifactPath",
    "registryRefs",
    "inputFingerprint",
    "mode",
    "decision",
    "confidenceBand",
    "inspectedInputs",
    "riskSummary",
    "calibrationState",
    "executionBoundary",
    "deliberation",
    "outputTiers",
    "permissionEscalationsRequested",
    "permissionEscalationsApproved",
    "guardrailRecommendations",
    "override",
    "sensitivityReview",
    "artifacts",
    "qualityFollowup"
)

foreach ($field in $requiredTopLevel) {
    if (-not (Test-HasProperty -Object $record -Name $field)) {
        throw "Missing required field '$field' in run record."
    }
}

if ($record.runId -notmatch '^pmx-[a-z0-9\-]+-\d{8}T\d{6}Z-[a-z0-9]{6}$') {
    throw "Run ID format is invalid: $($record.runId)"
}

$allowedDecisions = @("Pass", "Warn", "Block")
if ($allowedDecisions -notcontains $record.decision) {
    throw "Decision must be one of: $($allowedDecisions -join ', ')"
}

$allowedModes = @("release-risk-gating", "architecture-validation")
if ($allowedModes -notcontains $record.mode) {
    throw "Mode must be one of: $($allowedModes -join ', ')"
}

$allowedTaskCategories = @("risk-analysis", "calibration")
if ($allowedTaskCategories -notcontains $record.taskCategory) {
    throw "Task category must be one of: $($allowedTaskCategories -join ', ')"
}

$requiredArtifactFields = @(
    "summaryShort",
    "summaryStandard",
    "summaryExec",
    "riskRegister",
    "runRecord",
    "analysis",
    "approvals",
    "retention",
    "evidenceIndex",
    "deliberation"
)

foreach ($field in $requiredArtifactFields) {
    if (-not (Test-HasProperty -Object $record.artifacts -Name $field)) {
        throw "Missing required artifact field '$field'."
    }
}

if ($record.deliberation.rubric.gradingScale -ne "1-5") {
    throw "Deliberation rubric grading scale must be '1-5'."
}

$rubricFields = @(
    "confidence",
    "evidenceStrength",
    "riskSeverity",
    "evidenceCompleteness",
    "disagreementLevel",
    "policyFit",
    "decisionSensitivity"
)

foreach ($field in $rubricFields) {
    if (-not (Test-HasProperty -Object $record.deliberation.rubric -Name $field)) {
        throw "Missing deliberation rubric field '$field'."
    }

    $value = [int]$record.deliberation.rubric.$field
    if ($value -lt 1 -or $value -gt 5) {
        throw "Rubric field '$field' must be within 1-5."
    }
}

$allowedPromotionStates = @("trusted", "provisional", "excluded")
if ($allowedPromotionStates -notcontains $record.calibrationState.promotionState) {
    throw "Promotion state must be one of: $($allowedPromotionStates -join ', ')"
}

Write-Output ([pscustomobject]@{
    Valid = $true
    RunId = $record.runId
    Decision = $record.decision
})
