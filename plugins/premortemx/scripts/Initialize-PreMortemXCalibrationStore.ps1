[CmdletBinding()]
param(
    [string]$DatabasePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $DatabasePath) {
    $DatabasePath = Join-Path $pluginRoot "calibration\\premortemx-calibration.sqlite"
}

$pythonScript = Join-Path $pluginRoot "scripts\\lib\\premortemx_calibration_store.py"
$pythonCandidates = @(
    "python",
    "py"
)

$lastError = $null
foreach ($candidate in $pythonCandidates) {
    try {
        if ($candidate -eq "py") {
            $output = & $candidate -3 $pythonScript init-db --db-path $DatabasePath 2>&1
        }
        else {
            $output = & $candidate $pythonScript init-db --db-path $DatabasePath 2>&1
        }

        if ($LASTEXITCODE -eq 0) {
            $output | Write-Output
            return
        }
        $lastError = ($output | Out-String)
    }
    catch {
        $lastError = $_.Exception.Message
    }
}

throw "Unable to initialize calibration store. $lastError"
