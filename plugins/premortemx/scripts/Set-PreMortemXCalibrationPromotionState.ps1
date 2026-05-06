[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$CaseId,

    [Parameter(Mandatory = $true)]
    [ValidateSet("trusted", "provisional", "excluded")]
    [string]$PromotionState,

    [string]$ChangedBy = "codex",

    [string]$Reason = "manual-state-change",

    [string]$DatabasePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $DatabasePath) {
    $DatabasePath = Join-Path $pluginRoot "calibration\\premortemx-calibration.sqlite"
}

$pythonScript = Join-Path $pluginRoot "scripts\\lib\\premortemx_calibration_store.py"
$result = & python $pythonScript set-promotion-state --db-path $DatabasePath --case-id $CaseId --promotion-state $PromotionState --changed-by $ChangedBy --reason $Reason 2>&1
if ($LASTEXITCODE -ne 0) {
    throw ($result | Out-String)
}

$result | Write-Output
