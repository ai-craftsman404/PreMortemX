[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RunRecordPath,

    [string]$SpecialistInputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $RunRecordPath)) {
    throw "Run record not found: $RunRecordPath"
}

$record = Get-Content -LiteralPath $RunRecordPath -Raw | ConvertFrom-Json
$runDir = Split-Path -Parent $RunRecordPath
$deliberationPath = Join-Path $runDir "deliberation.json"

function Get-DecisionRank {
    param([string]$Decision)

    switch ($Decision) {
        "Pass" { return 1 }
        "Warn" { return 2 }
        "Block" { return 3 }
        default { return 0 }
    }
}

function Get-DecisionFromRank {
    param([int]$Rank)

    switch ($Rank) {
        1 { return "Pass" }
        2 { return "Warn" }
        3 { return "Block" }
        default { return "Warn" }
    }
}

function Get-ConfidenceBand {
    param([int]$Confidence)

    if ($Confidence -le 1) { return "Very Low" }
    if ($Confidence -eq 2) { return "Low" }
    if ($Confidence -eq 3) { return "Medium" }
    if ($Confidence -eq 4) { return "High" }
    return "Very High"
}

function New-DefaultSpecialist {
    param(
        [string]$Role,
        [string]$Decision
    )

    return [pscustomobject]@{
        role = $Role
        recommendation = $Decision
        summary = "Pending specialist review."
        evidenceRefs = @()
        rubric = @{
            confidence = 3
            evidenceStrength = 3
            riskSeverity = 3
            evidenceCompleteness = 3
            disagreementLevel = 1
            policyFit = 3
            decisionSensitivity = 3
        }
    }
}

$specialists = @()
if ($SpecialistInputPath) {
    if (-not (Test-Path -LiteralPath $SpecialistInputPath)) {
        throw "Specialist input file not found: $SpecialistInputPath"
    }

    $inputPayload = Get-Content -LiteralPath $SpecialistInputPath -Raw | ConvertFrom-Json
    if ($null -eq $inputPayload.specialists) {
        throw "Specialist input must contain a 'specialists' array."
    }
    $specialists = @($inputPayload.specialists)
}
else {
    foreach ($role in $record.deliberation.specialistRoles) {
        $specialists += New-DefaultSpecialist -Role $role -Decision $record.decision
    }
}

if (@($specialists).Count -eq 0) {
    throw "At least one specialist finding is required."
}

$decisionGroups = @($specialists | Group-Object recommendation)
$consensusDecision = $decisionGroups[0].Name
$maxConsensusCount = -1
foreach ($decisionGroup in $decisionGroups) {
    $groupCount = @($decisionGroup.Group).Count
    if ($groupCount -gt $maxConsensusCount -or ($groupCount -eq $maxConsensusCount -and $decisionGroup.Name -lt $consensusDecision)) {
        $consensusDecision = $decisionGroup.Name
        $maxConsensusCount = $groupCount
    }
}
$consensusGroup = @($specialists | Where-Object { $_.recommendation -eq $consensusDecision })
$minorityGroups = @($decisionGroups | Where-Object { $_.Name -ne $consensusDecision })
$minorityViews = @()
foreach ($minorityGroup in $minorityGroups) {
    $minorityViews += @($minorityGroup.Group)
}

$consensusEvidenceStrength = [math]::Round((($consensusGroup | ForEach-Object { [int]$_.rubric.evidenceStrength } | Measure-Object -Average).Average), 0)
$consensusConfidence = [math]::Round((($consensusGroup | ForEach-Object { [int]$_.rubric.confidence } | Measure-Object -Average).Average), 0)
$allEvidenceCompleteness = @($specialists | ForEach-Object { [int]$_.rubric.evidenceCompleteness })
$allConfidence = @($specialists | ForEach-Object { [int]$_.rubric.confidence })
$allSeverity = @($specialists | ForEach-Object { [int]$_.rubric.riskSeverity })
$allPolicyFit = @($specialists | ForEach-Object { [int]$_.rubric.policyFit })
$allSensitivity = @($specialists | ForEach-Object { [int]$_.rubric.decisionSensitivity })

$distinctDecisions = @($specialists.recommendation | Select-Object -Unique)
$disagreementLevel = switch (@($distinctDecisions).Count) {
    1 { 1 }
    2 { 3 }
    default { 5 }
}

$finalDecision = $consensusDecision
$overrideApplied = $false
$overrideReason = $null
$humanEscalationReasons = @()

$strongestMinority = $null
foreach ($minorityView in $minorityViews) {
    if ($null -eq $strongestMinority) {
        $strongestMinority = $minorityView
        continue
    }

    $candidateEvidence = [int]$minorityView.rubric.evidenceStrength
    $currentEvidence = [int]$strongestMinority.rubric.evidenceStrength
    $candidateRank = Get-DecisionRank -Decision $minorityView.recommendation
    $currentRank = Get-DecisionRank -Decision $strongestMinority.recommendation

    if ($candidateEvidence -gt $currentEvidence -or ($candidateEvidence -eq $currentEvidence -and $candidateRank -gt $currentRank)) {
        $strongestMinority = $minorityView
    }
}

if ($null -ne $strongestMinority) {
    $minorityEvidence = [int]$strongestMinority.rubric.evidenceStrength
    $minorityRank = Get-DecisionRank -Decision $strongestMinority.recommendation
    $consensusRank = Get-DecisionRank -Decision $consensusDecision

    if ($minorityEvidence -ge 4 -and ($minorityEvidence - $consensusEvidenceStrength) -ge 2 -and $minorityRank -gt $consensusRank) {
        $finalDecision = $strongestMinority.recommendation
        $overrideApplied = $true
        $overrideReason = "Evidence-gated override: minority specialist evidence materially exceeded the consensus evidence base."
    }
}

$minimumEvidenceCompleteness = ($allEvidenceCompleteness | Measure-Object -Minimum).Minimum
$minimumPolicyFit = ($allPolicyFit | Measure-Object -Minimum).Minimum
$maximumSeverity = ($allSeverity | Measure-Object -Maximum).Maximum
$maximumSensitivity = ($allSensitivity | Measure-Object -Maximum).Maximum
$overallConfidence = [int][math]::Round((($allConfidence | Measure-Object -Average).Average), 0)

if ($minimumEvidenceCompleteness -le 2 -and (Get-DecisionRank -Decision $finalDecision) -lt 2) {
    $finalDecision = "Warn"
    if (-not $overrideApplied) {
        $overrideApplied = $true
        $overrideReason = "Evidence-gated override: evidence completeness was too low to sustain a Pass."
    }
}

if ($disagreementLevel -ge 4 -and $overallConfidence -le 2 -and (Get-DecisionRank -Decision $finalDecision) -lt 2) {
    $finalDecision = "Warn"
    if (-not $overrideApplied) {
        $overrideApplied = $true
        $overrideReason = "Evidence-gated override: severe specialist disagreement and low confidence prevented a Pass."
    }
}

if ($maximumSeverity -ge 4 -and (@($specialists | Where-Object { [int]$_.rubric.riskSeverity -ge 4 -and [int]$_.rubric.evidenceStrength -ge 4 }).Count -ge 1)) {
    $finalDecision = "Block"
    if (-not $overrideApplied -or (Get-DecisionRank -Decision $finalDecision) -gt (Get-DecisionRank -Decision $consensusDecision)) {
        $overrideApplied = $true
        $overrideReason = "Severity-and-policy override: a credible high-severity risk met the escalation threshold."
    }
}

if ($minimumPolicyFit -le 2 -and (Get-DecisionRank -Decision $finalDecision) -lt 2) {
    $finalDecision = "Warn"
    if (-not $overrideApplied) {
        $overrideApplied = $true
        $overrideReason = "Severity-and-policy override: policy fit was too weak to sustain a Pass."
    }
}

if ($maximumSensitivity -ge 4 -and ($minimumEvidenceCompleteness -le 2 -or $disagreementLevel -ge 4)) {
    $humanEscalationReasons += "High-sensitivity case retains unresolved uncertainty."
}

if (($record.permissionEscalationsRequested | Measure-Object).Count -gt ($record.permissionEscalationsApproved | Measure-Object).Count) {
    $humanEscalationReasons += "Permission broadening remains unresolved."
}

$sortedRiskViews = @(
    $specialists |
    Sort-Object -Property @{ Expression = { ([int]$_.rubric.riskSeverity * 10) + [int]$_.rubric.evidenceStrength }; Descending = $true }
)
$topRisks = @(
    $sortedRiskViews |
    Select-Object -First 3 |
    ForEach-Object {
        [pscustomobject]@{
            role = $_.role
            recommendation = $_.recommendation
            summary = $_.summary
            evidenceRefs = @($_.evidenceRefs)
        }
    }
)

$record.deliberation.specialists = $specialists
$record.deliberation.agreement.consensusDecision = $consensusDecision
$record.deliberation.agreement.disagreementLevel = $disagreementLevel
$record.deliberation.agreement.summary = "Consensus began at $consensusDecision with disagreement level $disagreementLevel."
$record.deliberation.rubric.confidence = $overallConfidence
$record.deliberation.rubric.evidenceStrength = [int][math]::Round((($specialists | ForEach-Object { [int]$_.rubric.evidenceStrength } | Measure-Object -Average).Average), 0)
$record.deliberation.rubric.riskSeverity = $maximumSeverity
$record.deliberation.rubric.evidenceCompleteness = $minimumEvidenceCompleteness
$record.deliberation.rubric.disagreementLevel = $disagreementLevel
$record.deliberation.rubric.policyFit = $minimumPolicyFit
$record.deliberation.rubric.decisionSensitivity = $maximumSensitivity
$record.deliberation.overrideModel.overrideApplied = $overrideApplied
$record.deliberation.overrideModel.overrideReason = $overrideReason
$record.deliberation.overrideModel.humanEscalationRequired = (@($humanEscalationReasons).Count -gt 0)
$record.deliberation.overrideModel.humanEscalationReasons = $humanEscalationReasons
$record.deliberation.adjudication.finalDecision = $finalDecision
$record.deliberation.adjudication.finalConfidenceBand = Get-ConfidenceBand -Confidence $overallConfidence
$record.deliberation.adjudication.summary = if ($overrideApplied) { $overrideReason } else { "Orchestrator adjudicated to the consensus outcome without override." }
$record.deliberation.adjudication.supportingEvidence = @(
    $topRisks | ForEach-Object { @($_.evidenceRefs) } | Where-Object { $_ }
)
$record.deliberation.status = "completed"
$record.decision = $finalDecision
$record.confidenceBand = $record.deliberation.adjudication.finalConfidenceBand
$record.topRisks = $topRisks
$record.updatedAt = (Get-Date).ToUniversalTime().ToString("o")

$record | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $RunRecordPath
$record.deliberation | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $deliberationPath

[pscustomobject]@{
    runId = $record.runId
    finalDecision = $record.decision
    finalConfidenceBand = $record.confidenceBand
    overrideApplied = $overrideApplied
    humanEscalationRequired = (@($humanEscalationReasons).Count -gt 0)
} | ConvertTo-Json -Depth 8
