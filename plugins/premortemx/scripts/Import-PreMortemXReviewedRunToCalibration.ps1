[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RunRecordPath,

    [ValidateSet("trusted", "provisional", "excluded")]
    [string]$PromotionState = "provisional",

    [string]$DatasetVersion = "v1",

    [string]$DatabasePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $DatabasePath) {
    $DatabasePath = Join-Path $pluginRoot "calibration\\premortemx-calibration.sqlite"
}

$qualityLogPath = Join-Path $pluginRoot "registry\\quality-review-log.json"
$pythonScript = Join-Path $pluginRoot "scripts\\lib\\premortemx_calibration_store.py"

$result = & python $pythonScript import-reviewed-run --db-path $DatabasePath --run-record-path $RunRecordPath --quality-log-path $qualityLogPath --promotion-state $PromotionState --dataset-version $DatasetVersion 2>&1
if ($LASTEXITCODE -ne 0) {
    throw ($result | Out-String)
}

$payload = ($result | Out-String | ConvertFrom-Json)
$record = Get-Content -LiteralPath $RunRecordPath -Raw | ConvertFrom-Json
$record.calibrationState.promotionState = $PromotionState
$record.calibrationState.datasetVersion = $DatasetVersion
$record.calibrationState.caseId = $payload.caseId
$record.updatedAt = (Get-Date).ToUniversalTime().ToString("o")
$record | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $RunRecordPath

$payload | ConvertTo-Json -Depth 8
