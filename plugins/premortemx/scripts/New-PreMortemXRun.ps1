[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectSlug,

    [string]$PluginVersion = "0.3.0",

    [string]$Mode = "release-risk-gating",

    [string]$Decision = "Warn",

    [string]$ConfidenceBand = "Medium"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$runsRoot = Join-Path $pluginRoot "runs"
$registryRunsRoot = Join-Path $pluginRoot "registry\\runs"
$qualityLogPath = Join-Path $pluginRoot "registry\\quality-review-log.json"

$normalizedSlug = ($ProjectSlug.ToLowerInvariant() -replace '[^a-z0-9\-]+', '-') -replace '(^-+|-+$)', ''
if ([string]::IsNullOrWhiteSpace($normalizedSlug)) {
    throw "ProjectSlug must contain at least one alphanumeric character."
}

$allowedModes = @("release-risk-gating", "architecture-validation")
if ($allowedModes -notcontains $Mode) {
    throw "Mode must be one of: $($allowedModes -join ', ')"
}

$timestamp = (Get-Date).ToUniversalTime()
$timestampCompact = $timestamp.ToString("yyyyMMddTHHmmssZ")
$year = $timestamp.ToString("yyyy")
$month = $timestamp.ToString("MM")
$shortId = [guid]::NewGuid().ToString("N").Substring(0, 6)
$runId = "pmx-$normalizedSlug-$timestampCompact-$shortId"
$runDir = Join-Path (Join-Path (Join-Path $runsRoot $year) $month) $runId
$taskType = if ($Mode -eq "architecture-validation") { "architecture-review" } else { "premortem" }
$reportTitle = if ($Mode -eq "architecture-validation") { "PreMortemX Architecture Assessment" } else { "PreMortemX Release Assessment" }

New-Item -ItemType Directory -Path $runDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $runDir "attachments") -Force | Out-Null
New-Item -ItemType Directory -Path $registryRunsRoot -Force | Out-Null

$record = [ordered]@{
    schemaVersion = "1.0"
    runId = $runId
    pluginVersion = $PluginVersion
    createdAt = $timestamp.ToString("o")
    updatedAt = $timestamp.ToString("o")
    status = "initialized"
    projectSlug = $normalizedSlug
    taskType = $taskType
    taskCategory = "risk-analysis"
    initiator = "codex"
    executionMode = "skill+scripts"
    approvalMode = "adaptive"
    privacyMode = "privacy-first-hybrid"
    retentionClass = "standard"
    artifactPath = ("runs/{0}/{1}/{2}" -f $year, $month, $runId)
    registryRefs = @{
        indexKey = ("{0}-{1}/{2}" -f $year, $month, $runId)
    }
    inputFingerprint = @{
        promptHash = $null
        contextHash = $null
    }
    mode = $Mode
    routingType = "hybrid"
    decision = $Decision
    confidenceBand = $ConfidenceBand
    inspectedInputs = @{
        designDocs = @()
        implementationContext = @()
        releasePlan = @()
        testEvidence = @()
        architectureContext = @()
        dependencies = @()
        constraints = @()
    }
    riskSummary = @{
        high = 0
        medium = 0
        low = 0
    }
    topRisks = @()
    evidenceCoverage = "incomplete"
    calibrationState = @{
        promotionState = "excluded"
        datasetVersion = $null
        caseId = $null
    }
    executionBoundary = @{
        authorityMode = "local-only"
        advisoryMode = "cloud-only-advisory"
        advisoryDelegationAllowed = $true
        advisoryDelegationUsed = @()
    }
    deliberation = @{
        version = "3.0"
        adjudicatedBy = "orchestrator"
        status = "initialized"
        sharedRoles = @(
            "Evidence Auditor",
            "Decision Policy Reviewer",
            "Orchestrator"
        )
        specialistRoles = @(
            "Domain Risk Specialist",
            "Operational/Release Risk Specialist",
            "Security/Privacy Risk Specialist"
        )
        specialists = @()
        agreement = @{
            consensusDecision = $Decision
            disagreementLevel = 1
            summary = "Pending deliberation."
        }
        rubric = @{
            gradingScale = "1-5"
            confidence = 3
            evidenceStrength = 3
            riskSeverity = 3
            evidenceCompleteness = 3
            disagreementLevel = 1
            policyFit = 3
            decisionSensitivity = 3
            sourceProvenance = 3
            mitigationReadiness = 3
            calibratedPatternFit = 3
            contradictoryArtifactPressure = 1
        }
        overrideModel = @{
            defaultTrigger = "evidence-gated"
            backstopTrigger = "severity-and-policy"
            overrideApplied = $false
            overrideReason = $null
            humanEscalationRequired = $false
            humanEscalationReasons = @()
        }
        adjudication = @{
            finalDecision = $Decision
            finalConfidenceBand = $ConfidenceBand
            summary = "Pending orchestrator synthesis."
            supportingEvidence = @()
        }
    }
    warnReasons = @()
    blockReasons = @()
    outputTiers = @("short", "standard", "exec")
    permissionEscalationsRequested = @()
    permissionEscalationsApproved = @()
    guardrailRecommendations = @()
    override = @{
        applied = $false
        rationale = $null
        mitigationSteps = @()
        responsibleOwner = $null
    }
    sensitivityReview = @{
        likelySensitive = $false
        recommendedProtection = "none"
        encryptionUsed = $false
    }
    artifacts = @{
        summaryShort = "summary-short.md"
        summaryStandard = "summary-standard.md"
        summaryExec = "summary-exec.md"
        riskRegister = "risk-register.md"
        runRecord = "run-record.json"
        analysis = "analysis.json"
        approvals = "approvals.json"
        retention = "retention.json"
        override = $null
        evidenceIndex = "evidence-index.md"
        deliberation = "deliberation.json"
    }
    qualityFollowup = @{
        status = "pending"
        reviewDue = $null
        falsePositiveNotes = @()
        missedRiskNotes = @()
        outcomeNotes = @()
    }
}

$recordPath = Join-Path $runDir "run-record.json"
$record | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $recordPath

$nowText = $timestamp.ToString("yyyy-MM-dd HH:mm:ss 'UTC'")

@(
    "# $reportTitle"
    ""
    "- Run ID: $runId"
    "- Created: $nowText"
    "- Updated: $nowText"
    "- Mode: $Mode"
    "- Recommendation: $Decision"
    "- Confidence: $ConfidenceBand"
    ""
    "## Recommendation Snapshot"
    ""
    "- Decision pending refinement."
    ""
    "## Top Concerns"
    ""
    "- Add evidence-backed bullets here."
    ""
    "## Key Point Summary"
    ""
    "- Keep this section short and easy to scan."
) | Set-Content -LiteralPath (Join-Path $runDir "summary-short.md")

@(
    "# $reportTitle"
    ""
    "- Run ID: $runId"
    "- Created: $nowText"
    "- Updated: $nowText"
    "- Mode: $Mode"
    "- Recommendation: $Decision"
    "- Confidence: $ConfidenceBand"
    ""
    "## Recommendation Snapshot"
    ""
    "- Add the top-line judgment here."
    ""
    "## Top Blockers Or Concerns"
    ""
    "- Add detailed bullet points here."
    ""
    "## Mitigation Path"
    ""
    "- Add recommended mitigation steps here."
    ""
    "## Confidence And Evidence Note"
    ""
    "- Explain evidence quality and any important uncertainty."
    ""
    "## Key Point Summary"
    ""
    "- End with the shortest possible decision summary."
) | Set-Content -LiteralPath (Join-Path $runDir "summary-standard.md")

@(
    "# $reportTitle"
    ""
    "- Run ID: $runId"
    "- Created: $nowText"
    "- Recommendation: $Decision"
    "- Confidence: $ConfidenceBand"
    ""
    $(if ($Mode -eq "architecture-validation") { "## Architecture Recommendation" } else { "## Release Recommendation" })
    ""
    $(if ($Mode -eq "architecture-validation") { "- Add the executive-facing architecture recommendation here." } else { "- Add the executive-facing release recommendation here." })
    ""
    "## Top Blockers"
    ""
    "- Add the most important blockers or concerns here."
    ""
    "## Mitigation Path"
    ""
    "- Add the executive-facing mitigation path here."
    ""
    "## Key Point Summary"
    ""
    "- Keep this section brief."
) | Set-Content -LiteralPath (Join-Path $runDir "summary-exec.md")

@(
    $(if ($Mode -eq "architecture-validation") { "# PreMortemX Architecture Risk Register" } else { "# PreMortemX Risk Register" })
    ""
    "- Run ID: $runId"
    "- Created: $nowText"
    ""
    "## Scope Reviewed"
    ""
    "- List the inspected design, architecture, code, release, and test artifacts."
    ""
    "## Detailed Risks"
    ""
    "- Add one evidence-backed bullet per material risk."
    ""
    "## Evidence References"
    ""
    "- Link each material finding back to concrete evidence."
    ""
    "## Mitigations"
    ""
    "- Add mitigation bullets here."
    ""
    "## Unresolved Assumptions"
    ""
    "- Record material uncertainty here."
    ""
    "## Key Point Summary"
    ""
    "- Keep this section brief and scannable."
) | Set-Content -LiteralPath (Join-Path $runDir "risk-register.md")

(@{
    generatedAt = $timestamp.ToString("o")
    notes = @(
        "Structured internal analysis output belongs here.",
        "Keep machine-oriented reasoning concise and auditable."
    )
} | ConvertTo-Json -Depth 5) | Set-Content -LiteralPath (Join-Path $runDir "analysis.json")

($record.deliberation | ConvertTo-Json -Depth 10) | Set-Content -LiteralPath (Join-Path $runDir "deliberation.json")

(@{
    approvalsRequested = @()
    approvalsGranted = @()
    recommendation = "stay-conservative"
    notes = @("Permission escalation events belong here.")
} | ConvertTo-Json -Depth 5) | Set-Content -LiteralPath (Join-Path $runDir "approvals.json")

(@{
    likelySensitive = $false
    recommendation = "none"
    encryptionDecision = "not-requested"
    notes = @("Retention and sensitivity decisions belong here.")
} | ConvertTo-Json -Depth 5) | Set-Content -LiteralPath (Join-Path $runDir "retention.json")

@(
    "# Evidence Index"
    ""
    "- Run ID: $runId"
    ""
    "## Sources"
    ""
    "- Add the inspected evidence sources here."
) | Set-Content -LiteralPath (Join-Path $runDir "evidence-index.md")

if (-not (Test-Path -LiteralPath $qualityLogPath)) {
    (@{
        items = @()
    } | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $qualityLogPath
}

$result = [pscustomobject]@{
    RunId = $runId
    RunPath = $runDir
    RecordPath = $recordPath
}

$result | ConvertTo-Json -Depth 4
