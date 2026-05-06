[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

[pscustomobject]@{
    authorityMode = "local-only"
    advisoryMode = "cloud-only-advisory"
    alwaysLocal = @(
        "orchestrator-selection-and-synthesis",
        "evidence-handling",
        "final-decision",
        "approval-handling",
        "policy-changes",
        "audit-and-registry-writes"
    )
    optionallyDelegated = @(
        "adversarial-critique",
        "bounded-specialist-second-opinions",
        "calibration-batch-analysis"
    )
} | ConvertTo-Json -Depth 6
