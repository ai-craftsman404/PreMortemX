[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pluginRoot = Split-Path -Parent (Split-Path -Parent $scriptRoot)
$scriptsRoot = Join-Path $pluginRoot "scripts"
$calibrationDbPath = Join-Path $pluginRoot "calibration\\premortemx-calibration.sqlite"

$testsRun = 0

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

function Invoke-Script {
    param(
        [string]$ScriptName,
        [string[]]$Arguments
    )

    $scriptPath = Join-Path $scriptsRoot $ScriptName
    $stdoutPath = Join-Path ([System.IO.Path]::GetTempPath()) ("pmx-stdout-" + [guid]::NewGuid().ToString("N") + ".txt")
    $stderrPath = Join-Path ([System.IO.Path]::GetTempPath()) ("pmx-stderr-" + [guid]::NewGuid().ToString("N") + ".txt")

    try {
        $argumentList = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $scriptPath
        ) + $Arguments

        $process = Start-Process -FilePath "powershell" -ArgumentList $argumentList -Wait -PassThru -NoNewWindow -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath

        $stdout = if (Test-Path -LiteralPath $stdoutPath) { Get-Content -LiteralPath $stdoutPath -Raw } else { "" }
        $stderr = if (Test-Path -LiteralPath $stderrPath) { Get-Content -LiteralPath $stderrPath -Raw } else { "" }

        [pscustomobject]@{
            ExitCode = $process.ExitCode
            Output = (($stdout + "`n" + $stderr).Trim())
        }
    }
    finally {
        if (Test-Path -LiteralPath $stdoutPath) {
            Remove-Item -LiteralPath $stdoutPath -Force
        }
        if (Test-Path -LiteralPath $stderrPath) {
            Remove-Item -LiteralPath $stderrPath -Force
        }
    }
}

function Test-RunInitialization {
    $projectSlug = "sample-api"
    $result = Invoke-Script -ScriptName "New-PreMortemXRun.ps1" -Arguments @("-ProjectSlug", $projectSlug, "-Decision", "Warn")
    Assert-True ($result.ExitCode -eq 0) "Run initialization should succeed."

    $created = $result.Output | ConvertFrom-Json
    Assert-True ([string]::IsNullOrWhiteSpace($created.RunId) -eq $false) "RunId should be returned."
    Assert-True (Test-Path -LiteralPath $created.RunPath) "Run directory should exist."
    Assert-True (Test-Path -LiteralPath (Join-Path $created.RunPath "run-record.json")) "Run record should exist."
    Assert-True (Test-Path -LiteralPath (Join-Path $created.RunPath "deliberation.json")) "Deliberation template should exist."
    $script:testsRun++

    return $created
}

function Test-ArchitectureRunInitialization {
    $projectSlug = "sample-arch"
    $result = Invoke-Script -ScriptName "New-PreMortemXRun.ps1" -Arguments @("-ProjectSlug", $projectSlug, "-Mode", "architecture-validation", "-Decision", "Warn")
    Assert-True ($result.ExitCode -eq 0) "Architecture run initialization should succeed."

    $created = $result.Output | ConvertFrom-Json
    $record = Get-Content -LiteralPath $created.RecordPath -Raw | ConvertFrom-Json
    $summary = Get-Content -LiteralPath (Join-Path $created.RunPath "summary-standard.md") -Raw

    Assert-True ($record.mode -eq "architecture-validation") "Architecture mode should be recorded."
    Assert-True ($record.taskType -eq "architecture-review") "Architecture task type should be recorded."
    Assert-True ($record.taskCategory -eq "risk-analysis") "Architecture task category should default to risk-analysis."
    Assert-True ($summary -match "PreMortemX Architecture Assessment") "Architecture summary title should be used."
    $script:testsRun++

    return $created
}

function Test-RunRecordValidation {
    param([pscustomobject]$CreatedRun)

    $result = Invoke-Script -ScriptName "Test-PreMortemXRunRecord.ps1" -Arguments @("-RunRecordPath", $CreatedRun.RecordPath)
    Assert-True ($result.ExitCode -eq 0) "Run record validation should succeed."
    $script:testsRun++
}

function Test-Deliberation {
    param([pscustomobject]$CreatedRun)

    $specialistInputPath = Join-Path $CreatedRun.RunPath "specialists-test.json"
    @'
{
  "specialists": [
    {
      "role": "Domain Risk Specialist",
      "recommendation": "Warn",
      "summary": "The delivery shape is fragile.",
      "evidenceRefs": ["design/spec.md"],
      "rubric": {
        "confidence": 2,
        "evidenceStrength": 2,
        "riskSeverity": 3,
        "evidenceCompleteness": 2,
        "disagreementLevel": 4,
        "policyFit": 3,
        "decisionSensitivity": 3
      }
    },
    {
      "role": "Operational/Release Risk Specialist",
      "recommendation": "Pass",
      "summary": "Operational controls look manageable.",
      "evidenceRefs": ["ops/checklist.md"],
      "rubric": {
        "confidence": 2,
        "evidenceStrength": 2,
        "riskSeverity": 2,
        "evidenceCompleteness": 2,
        "disagreementLevel": 4,
        "policyFit": 3,
        "decisionSensitivity": 4
      }
    },
    {
      "role": "Security/Privacy Risk Specialist",
      "recommendation": "Block",
      "summary": "Sensitive path lacks enough evidence controls.",
      "evidenceRefs": ["security/review.md"],
      "rubric": {
        "confidence": 4,
        "evidenceStrength": 5,
        "riskSeverity": 5,
        "evidenceCompleteness": 4,
        "disagreementLevel": 4,
        "policyFit": 2,
        "decisionSensitivity": 5
      }
    }
  ]
}
'@ | Set-Content -LiteralPath $specialistInputPath

    $result = Invoke-Script -ScriptName "Invoke-PreMortemXDeliberation.ps1" -Arguments @("-RunRecordPath", $CreatedRun.RecordPath, "-SpecialistInputPath", $specialistInputPath)
    Assert-True ($result.ExitCode -eq 0) "Deliberation should succeed."

    $payload = $result.Output | ConvertFrom-Json
    $record = Get-Content -LiteralPath $CreatedRun.RecordPath -Raw | ConvertFrom-Json
    Assert-True ($payload.finalDecision -eq "Block") "Deliberation should escalate to Block."
    Assert-True ($record.deliberation.status -eq "completed") "Deliberation status should be completed."
    Assert-True ($record.deliberation.overrideModel.overrideApplied -eq $true) "Override model should record an override."
    Assert-True ($record.deliberation.overrideModel.humanEscalationRequired -eq $true) "High-sensitivity uncertainty should require human escalation."
    $script:testsRun++
}

function Test-RegistryUpdate {
    param([pscustomobject]$CreatedRun)

    $result = Invoke-Script -ScriptName "Update-PreMortemXRegistry.ps1" -Arguments @("-RunRecordPath", $CreatedRun.RecordPath)
    Assert-True ($result.ExitCode -eq 0) "Registry update should succeed."

    $indexPath = Join-Path $pluginRoot "registry\\runs\\index.jsonl"
    Assert-True (Test-Path -LiteralPath $indexPath) "Registry index should exist."
    $content = Get-Content -LiteralPath $indexPath -Raw
    Assert-True ($content -match $CreatedRun.RunId) "Registry should contain the run ID."
    Assert-True ($content -match "risk-analysis") "Registry should contain task category."
    $script:testsRun++
}

function Test-InvalidDecisionFailsValidation {
    param([pscustomobject]$CreatedRun)

    $record = Get-Content -LiteralPath $CreatedRun.RecordPath -Raw | ConvertFrom-Json
    $record.decision = "Maybe"
    $record | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $CreatedRun.RecordPath

    $result = Invoke-Script -ScriptName "Test-PreMortemXRunRecord.ps1" -Arguments @("-RunRecordPath", $CreatedRun.RecordPath)
    Assert-True ($result.ExitCode -ne 0) "Invalid decision should fail validation."
    $script:testsRun++
}

function Test-RegistrySummary {
    $result = Invoke-Script -ScriptName "Get-PreMortemXRegistrySummary.ps1" -Arguments @()
    Assert-True ($result.ExitCode -eq 0) "Registry summary should succeed."
    $summary = $result.Output | ConvertFrom-Json
    Assert-True ($summary.totalRuns -ge 1) "Registry summary should report at least one run."
    Assert-True ($summary.byDecision.Block -ge 1) "Registry summary should count Block decisions."
    Assert-True ($summary.pendingQualityFollowup -ge 1) "Registry summary should report pending quality follow-up before reviews."
    $script:testsRun++
}

function Test-RegistryViewsBuild {
    $result = Invoke-Script -ScriptName "Build-PreMortemXRegistryViews.ps1" -Arguments @()
    Assert-True ($result.ExitCode -eq 0) "Registry view build should succeed."

    $viewsRoot = Join-Path $pluginRoot "registry\\views"
    Assert-True (Test-Path -LiteralPath (Join-Path $viewsRoot "latest-by-project.json")) "latest-by-project view should exist."
    Assert-True (Test-Path -LiteralPath (Join-Path $viewsRoot "attention-queue.json")) "attention-queue view should exist."
    Assert-True (Test-Path -LiteralPath (Join-Path $viewsRoot "dashboard.md")) "dashboard view should exist."
    $script:testsRun++
}

function Test-GuardrailRecommendations {
    $result = Invoke-Script -ScriptName "Get-PreMortemXGuardrailRecommendations.ps1" -Arguments @("-ProjectSlug", "sample-api")
    Assert-True ($result.ExitCode -eq 0) "Guardrail recommendation script should succeed."
    $payload = $result.Output | ConvertFrom-Json
    Assert-True ($payload.reviewedRuns -ge 1) "Guardrail recommendation should review at least one run."
    Assert-True (@($payload.recommendations).Count -ge 1) "Guardrail recommendation should emit at least one recommendation."
    $script:testsRun++
}

function Test-QualityReviewUpdate {
    param([pscustomobject]$CreatedRun)

    $result = Invoke-Script -ScriptName "Update-PreMortemXQualityReview.ps1" -Arguments @(
        "-RunRecordPath", $CreatedRun.RecordPath,
        "-ReviewOutcome", "accurate",
        "-Reviewer", "adversarial-evaluator",
        "-OutcomeNotes", "Validated-after-manual-review."
    )
    Assert-True ($result.ExitCode -eq 0) "Quality review update should succeed."

    $qualityLogPath = Join-Path $pluginRoot "registry\\quality-review-log.json"
    $qualityLog = Get-Content -LiteralPath $qualityLogPath -Raw | ConvertFrom-Json
    Assert-True (@($qualityLog.items).Count -ge 1) "Quality review log should contain at least one item."
    $matchingReview = @($qualityLog.items | Where-Object { $_.runId -eq $CreatedRun.RunId } | Select-Object -First 1)
    Assert-True (@($matchingReview).Count -eq 1) "Matching quality review should exist."
    Assert-True ($matchingReview[0].reviewer -eq "adversarial-evaluator") "Reviewer should be recorded."
    $script:testsRun++
}

function Test-TrendSummary {
    $result = Invoke-Script -ScriptName "Get-PreMortemXTrendSummary.ps1" -Arguments @()
    Assert-True ($result.ExitCode -eq 0) "Trend summary should succeed."
    $payload = $result.Output | ConvertFrom-Json
    Assert-True ($payload.totalReviewed -ge 1) "Trend summary should report reviewed items."
    Assert-True ($payload.byOutcome.accurate -ge 1) "Trend summary should count accurate reviews."
    $script:testsRun++
}

function Test-CalibrationStoreInitialization {
    $result = Invoke-Script -ScriptName "Initialize-PreMortemXCalibrationStore.ps1" -Arguments @("-DatabasePath", $calibrationDbPath)
    Assert-True ($result.ExitCode -eq 0) "Calibration store initialization should succeed."
    Assert-True (Test-Path -LiteralPath $calibrationDbPath) "Calibration database should exist."
    $script:testsRun++
}

function Test-ReviewedRunImportToCalibration {
    param([pscustomobject]$CreatedRun)

    $result = Invoke-Script -ScriptName "Import-PreMortemXReviewedRunToCalibration.ps1" -Arguments @(
        "-RunRecordPath", $CreatedRun.RecordPath,
        "-PromotionState", "trusted",
        "-DatasetVersion", "v3a-seed",
        "-DatabasePath", $calibrationDbPath
    )
    Assert-True ($result.ExitCode -eq 0) "Reviewed run import should succeed."
    $payload = $result.Output | ConvertFrom-Json
    Assert-True ($payload.promotionState -eq "trusted") "Imported case should be trusted."

    $record = Get-Content -LiteralPath $CreatedRun.RecordPath -Raw | ConvertFrom-Json
    Assert-True ($record.calibrationState.promotionState -eq "trusted") "Run record should track trusted promotion."
    Assert-True ($record.calibrationState.datasetVersion -eq "v3a-seed") "Run record should track dataset version."
    $script:testsRun++
}

function Test-CalibrationSummary {
    $result = Invoke-Script -ScriptName "Get-PreMortemXCalibrationSummary.ps1" -Arguments @("-DatabasePath", $calibrationDbPath)
    Assert-True ($result.ExitCode -eq 0) "Calibration summary should succeed."
    $payload = $result.Output | ConvertFrom-Json
    Assert-True ($payload.totalCases -ge 1) "Calibration summary should report at least one case."
    Assert-True ($payload.byPromotionState.trusted -ge 1) "Calibration summary should count trusted cases."
    $script:testsRun++
}

function Test-PromotionStateChange {
    param([pscustomobject]$CreatedRun)

    $result = Invoke-Script -ScriptName "Set-PreMortemXCalibrationPromotionState.ps1" -Arguments @(
        "-CaseId", $CreatedRun.RunId,
        "-PromotionState", "provisional",
        "-ChangedBy", "codex",
        "-Reason", "testing-state-change",
        "-DatabasePath", $calibrationDbPath
    )
    Assert-True ($result.ExitCode -eq 0) "Promotion state change should succeed."
    Assert-True ($result.Output -match "provisional") "Promotion state output should mention provisional."
    $script:testsRun++
}

function Test-CalibrationChangeApprovalFlow {
    $request = Invoke-Script -ScriptName "Request-PreMortemXCalibrationChange.ps1" -Arguments @(
        "-ChangeTier", "TierB",
        "-ChangeType", "confidence-band-tuning",
        "-ProposedValue", "{""confidence"":4}",
        "-Reason", "regression-tuning",
        "-RequestedBy", "codex",
        "-DatabasePath", $calibrationDbPath
    )
    Assert-True ($request.ExitCode -eq 0) "Calibration change request should succeed."
    $requestPayload = $request.Output | ConvertFrom-Json

    $approval = Invoke-Script -ScriptName "Approve-PreMortemXCalibrationChange.ps1" -Arguments @(
        "-ChangeRequestId", $requestPayload.changeRequestId,
        "-ApprovalScope", "session",
        "-ApprovalDecision", "approved",
        "-ApprovedBy", "codex",
        "-ApprovalNote", "bounded-test-approval",
        "-DatabasePath", $calibrationDbPath
    )
    Assert-True ($approval.ExitCode -eq 0) "Calibration change approval should succeed."
    Assert-True ($approval.Output -match "approved") "Approval output should indicate approved."
    $script:testsRun++
}

function Test-AdvisoryDelegationPlan {
    $result = Invoke-Script -ScriptName "Get-PreMortemXAdvisoryDelegationPlan.ps1" -Arguments @()
    Assert-True ($result.ExitCode -eq 0) "Advisory delegation plan should succeed."
    $payload = $result.Output | ConvertFrom-Json
    Assert-True ($payload.authorityMode -eq "local-only") "Authority mode should stay local-only."
    Assert-True (@($payload.optionallyDelegated).Count -ge 1) "Optional delegation list should be populated."
    $script:testsRun++
}

function Test-QualityAwareRegistrySummary {
    $result = Invoke-Script -ScriptName "Get-PreMortemXRegistrySummary.ps1" -Arguments @()
    Assert-True ($result.ExitCode -eq 0) "Quality-aware registry summary should succeed."
    $payload = $result.Output | ConvertFrom-Json
    Assert-True ($payload.totalReviewed -ge 1) "Registry summary should include reviewed counts."
    Assert-True ($payload.byReviewOutcome.accurate -ge 1) "Registry summary should include review outcomes."
    Assert-True ($payload.pendingQualityFollowup -ge 0) "Registry summary should include pending quality follow-up count."
    $script:testsRun++
}

function Test-QualityAwareRegistryViews {
    $viewsRoot = Join-Path $pluginRoot "registry\\views"
    $dashboardPath = Join-Path $viewsRoot "dashboard.md"
    $content = Get-Content -LiteralPath $dashboardPath -Raw
    Assert-True ($content -match "Reviewed runs:") "Dashboard should include reviewed run counts."
    Assert-True ($content -match "Pending quality follow-up:") "Dashboard should include pending quality follow-up."
    $script:testsRun++
}

$indexPath = Join-Path $pluginRoot "registry\\runs\\index.jsonl"
$qualityLogPath = Join-Path $pluginRoot "registry\\quality-review-log.json"
$viewsRoot = Join-Path $pluginRoot "registry\\views"

$indexBackup = if (Test-Path -LiteralPath $indexPath) { Get-Content -LiteralPath $indexPath -Raw } else { $null }
$qualityBackup = if (Test-Path -LiteralPath $qualityLogPath) { Get-Content -LiteralPath $qualityLogPath -Raw } else { $null }
$viewsBackup = if (Test-Path -LiteralPath $viewsRoot) { $true } else { $false }

$createdRun = Test-RunInitialization
$architectureRun = Test-ArchitectureRunInitialization
try {
    Test-RunRecordValidation -CreatedRun $createdRun
    Test-RunRecordValidation -CreatedRun $architectureRun
    Test-Deliberation -CreatedRun $createdRun
    Test-RegistryUpdate -CreatedRun $createdRun
    Test-RegistryUpdate -CreatedRun $architectureRun
    Test-RegistrySummary
    Test-RegistryViewsBuild
    Test-QualityReviewUpdate -CreatedRun $createdRun
    Test-GuardrailRecommendations
    Test-TrendSummary
    Test-CalibrationStoreInitialization
    Test-ReviewedRunImportToCalibration -CreatedRun $createdRun
    Test-CalibrationSummary
    Test-PromotionStateChange -CreatedRun $createdRun
    Test-CalibrationChangeApprovalFlow
    Test-AdvisoryDelegationPlan
    Test-QualityAwareRegistrySummary
    Test-RegistryViewsBuild
    Test-QualityAwareRegistryViews
    Test-InvalidDecisionFailsValidation -CreatedRun $createdRun
}
finally {
    if ($null -eq $indexBackup) {
        if (Test-Path -LiteralPath $indexPath) {
            Remove-Item -LiteralPath $indexPath -Force
        }
    }
    else {
        Set-Content -LiteralPath $indexPath -Value $indexBackup
    }

    if ($null -eq $qualityBackup) {
        if (Test-Path -LiteralPath $qualityLogPath) {
            Remove-Item -LiteralPath $qualityLogPath -Force
        }
    }
    else {
        Set-Content -LiteralPath $qualityLogPath -Value $qualityBackup
    }

    if (-not $viewsBackup) {
        if (Test-Path -LiteralPath $viewsRoot) {
            Remove-Item -LiteralPath $viewsRoot -Recurse -Force
        }
    }

    if (Test-Path -LiteralPath $calibrationDbPath) {
        Remove-Item -LiteralPath $calibrationDbPath -Force
    }

    $calibrationRoot = Split-Path -Parent $calibrationDbPath
    if (Test-Path -LiteralPath $calibrationRoot) {
        $children = @(Get-ChildItem -LiteralPath $calibrationRoot -Force)
        if ($children.Count -eq 0) {
            Remove-Item -LiteralPath $calibrationRoot -Force
        }
    }

    if ($createdRun -and (Test-Path -LiteralPath $createdRun.RunPath)) {
        Remove-Item -LiteralPath $createdRun.RunPath -Recurse -Force
    }
    if ($architectureRun -and (Test-Path -LiteralPath $architectureRun.RunPath)) {
        Remove-Item -LiteralPath $architectureRun.RunPath -Recurse -Force
    }
}

Write-Host "PreMortemX script tests passed: $testsRun"
