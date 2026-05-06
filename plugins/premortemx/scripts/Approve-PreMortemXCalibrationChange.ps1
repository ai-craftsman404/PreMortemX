[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ChangeRequestId,

    [Parameter(Mandatory = $true)]
    [ValidateSet("session", "persistent", "manual")]
    [string]$ApprovalScope,

    [Parameter(Mandatory = $true)]
    [ValidateSet("approved", "rejected")]
    [string]$ApprovalDecision,

    [string]$ApprovedBy = "codex",

    [string]$ApprovalNote = "",

    [string]$DatabasePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $DatabasePath) {
    $DatabasePath = Join-Path $pluginRoot "calibration\\premortemx-calibration.sqlite"
}

$pythonScript = Join-Path $pluginRoot "scripts\\lib\\premortemx_calibration_store.py"
$result = & python $pythonScript approve-change --db-path $DatabasePath --change-request-id $ChangeRequestId --approved-by $ApprovedBy --approval-scope $ApprovalScope --approval-decision $ApprovalDecision --approval-note $ApprovalNote 2>&1
if ($LASTEXITCODE -ne 0) {
    throw ($result | Out-String)
}

$result | Write-Output
