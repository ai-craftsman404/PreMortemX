[CmdletBinding()]
param(
    [string]$ProjectSlug,
    [ValidateSet("all", "release-risk-gating", "architecture-validation")]
    [string]$Mode = "all"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$runsRoot = Join-Path $pluginRoot "runs"

if (-not (Test-Path -LiteralPath $runsRoot)) {
    [pscustomobject]@{
        recommendations = @()
        reviewedRuns = 0
    } | ConvertTo-Json -Depth 8
    return
}

$records = @()
Get-ChildItem -LiteralPath $runsRoot -Recurse -Filter "run-record.json" -File | ForEach-Object {
    $records += (Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json)
}

if ($ProjectSlug) {
    $records = @($records | Where-Object { $_.projectSlug -eq $ProjectSlug })
}

if ($Mode -ne "all") {
    $records = @($records | Where-Object { $_.mode -eq $Mode })
}

$recommendations = @()

foreach ($group in ($records | Group-Object projectSlug, mode)) {
    $items = @($group.Group | Sort-Object createdAt -Descending)
    if ($items.Count -eq 0) {
        continue
    }

    $latest = $items[0]
    $warnOrBlockCount = @($items | Where-Object { $_.decision -in @("Warn", "Block") }).Count
    $incompleteCoverageCount = @($items | Where-Object { $_.evidenceCoverage -eq "incomplete" }).Count
    $requestedCount = 0
    $approvedCount = 0

    foreach ($item in $items) {
        if ($null -ne $item.permissionEscalationsRequested) {
            $requestedCount += @($item.permissionEscalationsRequested).Count
        }
        if ($null -ne $item.permissionEscalationsApproved) {
            $approvedCount += @($item.permissionEscalationsApproved).Count
        }
    }

    $recommendation = if ($warnOrBlockCount -ge 2 -and $incompleteCoverageCount -ge 2) {
        "Consider a broader approved evidence scope for this project/mode on the next run."
    }
    elseif ($requestedCount -gt $approvedCount) {
        "Review pending permission needs before the next run; prior requests exceeded approvals."
    }
    else {
        "Keep the current conservative scope unless the next run surfaces repeated evidence gaps."
    }

    $recommendations += [pscustomobject]@{
        projectSlug = $latest.projectSlug
        mode = $latest.mode
        reviewedRuns = $items.Count
        warnOrBlockRuns = $warnOrBlockCount
        incompleteEvidenceRuns = $incompleteCoverageCount
        requestedEscalations = $requestedCount
        approvedEscalations = $approvedCount
        recommendation = $recommendation
    }
}

[pscustomobject]@{
    reviewedRuns = $records.Count
    recommendations = $recommendations
} | ConvertTo-Json -Depth 8
