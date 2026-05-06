[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("TierA", "TierB", "TierC")]
    [string]$ChangeTier,

    [Parameter(Mandatory = $true)]
    [string]$ChangeType,

    [Parameter(Mandatory = $true)]
    [string]$ProposedValue,

    [string]$Reason = "calibration-adjustment-request",

    [string]$RequestedBy = "codex",

    [string]$DatabasePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $DatabasePath) {
    $DatabasePath = Join-Path $pluginRoot "calibration\\premortemx-calibration.sqlite"
}

$changeRequestId = "pmx-change-" + [guid]::NewGuid().ToString("N").Substring(0, 10)
$pythonScript = Join-Path $pluginRoot "scripts\\lib\\premortemx_calibration_store.py"
$result = & python $pythonScript request-change --db-path $DatabasePath --change-request-id $changeRequestId --requested-by $RequestedBy --change-tier $ChangeTier --change-type $ChangeType --proposed-value $ProposedValue --reason $Reason 2>&1
if ($LASTEXITCODE -ne 0) {
    throw ($result | Out-String)
}

$result | Write-Output
