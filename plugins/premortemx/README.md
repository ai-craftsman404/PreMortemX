# PreMortemX

PreMortemX is a Codex plugin for evidence-backed pre-mortem release gating and architecture validation. It helps Codex users inspect release or architecture bundles, validate risk claims against evidence, and produce readable Pass / Warn / Block decisions with structured override support.

## Product positioning

PreMortemX is not trying to invent a new risk-assessment discipline.

Its differentiator is that it applies established risk-assessment practice through an AI operating model:
- specialist AI agents working from distinct risk lenses
- orchestrated deliberation instead of naive vote counting
- final adjudication by a central orchestrator
- evidence-backed recommendations and decisions
- calibration and maintenance over time using curated reviewed signals

This is the main adoption story for v3:
- familiar and disciplined risk-assessment structure
- faster and more scalable execution through specialist AI collaboration
- human-governed, auditable outcomes instead of opaque model intuition

## V3 highlights

- multi-agent deliberation with orchestrator adjudication
- rubric-backed override logic with internal `1-5` grading
- adjudicated user output instead of exposed internal debate
- SQLite-backed calibration dataset store
- reviewed-run promotion states: `trusted`, `provisional`, `excluded`
- calibration change requests and approvals
- local-only authority with optional cloud-advisory edges

## What it does

- release-first pre-mortem analysis
- architecture validation before implementation
- docs + code + test evidence grounding
- tiered human-facing reports
- machine-readable run records
- structured Block override capture
- privacy-first retention and adaptive approvals
- stronger local registry summaries
- local guardrail-memory recommendations
- quality-review updates and trend summaries
- quality-aware registry dashboards

## V3 scope

- release risk gating
- architecture validation
- hybrid routing with targeted Q&A when confidence is low
- local-first run artifacts and registry index
- local registry summary view
- optional sensitive-artifact encryption decision left to the human
- multi-agent adjudication recorded in `deliberation.json`
- calibration store and promotion flow for reviewed runs
- no mandatory external services

## Plugin structure

```text
plugins/premortemx/
  .codex-plugin/plugin.json
  skills/
  scripts/
  registry/
  runs/
  calibration/
```

## Skills

- `premortemx`: main release-risk pre-mortem skill

## Scripts

- `New-PreMortemXRun.ps1`: create a new run directory, run record, and report templates
- `Update-PreMortemXRegistry.ps1`: append a run to the local registry index
- `Test-PreMortemXRunRecord.ps1`: validate required run-record fields and decision format
- `Invoke-PreMortemXDeliberation.ps1`: run orchestrator-led specialist adjudication and update deliberation artifacts
- `Get-PreMortemXRegistrySummary.ps1`: summarize runs by mode and decision
- `Build-PreMortemXRegistryViews.ps1`: build materialized registry views for operators
- `Get-PreMortemXGuardrailRecommendations.ps1`: recommend whether to stay conservative or consider broader approved access based on prior runs
- `Update-PreMortemXQualityReview.ps1`: record later outcome review for a run
- `Get-PreMortemXTrendSummary.ps1`: summarize quality outcomes across reviewed runs
- `Initialize-PreMortemXCalibrationStore.ps1`: create the local SQLite calibration store
- `Import-PreMortemXReviewedRunToCalibration.ps1`: promote a reviewed run into calibration storage
- `Set-PreMortemXCalibrationPromotionState.ps1`: change calibration promotion state with audit logging
- `Request-PreMortemXCalibrationChange.ps1`: create a calibration change request
- `Approve-PreMortemXCalibrationChange.ps1`: approve or reject a calibration change request
- `Get-PreMortemXCalibrationSummary.ps1`: summarize calibration cases and change requests
- `Get-PreMortemXAdvisoryDelegationPlan.ps1`: show the local-authority and optional-advisory delegation boundary

Registry views now also fold in quality-review outcomes and pending follow-up counts.

## Run artifacts

PreMortemX uses run directories under:

```text
plugins/premortemx/runs/YYYY/MM/<run-id>/
```

Typical artifacts:

- `summary-short.md`
- `summary-standard.md`
- `summary-exec.md`
- `risk-register.md`
- `run-record.json`
- `analysis.json`
- `approvals.json`
- `retention.json`
- `override.md`
- `evidence-index.md`
- `deliberation.json`

Registry files:

- `registry/runs/index.jsonl`
- `registry/quality-review-log.json`

Calibration files:

- `calibration/premortemx-calibration.sqlite`

## Decision model

- `Pass`: adequate evidence, low residual risk, no warn/block rule triggered
- `Warn`: meaningful uncertainty or credible medium risk
- `Block`: credible high-severity risk or aggregate threshold breach

A `Block` can be overridden by a human, but the override must preserve:
- rationale
- mitigation steps
- responsible owner

Supported modes:
- `release-risk-gating`
- `architecture-validation`

## Install and discovery

Typical local install flow:

1. Download or clone the plugin package.
2. Open the plugin workspace in Codex.
3. Install or enable `PreMortemX` from the Codex Plugins UI.
4. Invoke it in chat with `$premortemx`.

## Example prompts

- `$premortemx Run a pre-mortem on this release plan and tell me whether we should ship.`
- `$premortemx Validate this architecture and identify the top design risks before implementation.`
- `$premortemx Assess this design, diff summary, and test output for credible release blockers.`
- `$premortemx Override this block and record the rationale, mitigation, and owner.`
- `$premortemx Smoke test this plugin and confirm it is active.`

## Local testing

Run the script test suite:

```powershell
powershell -NoProfile -File .\plugins\premortemx\scripts\tests\Run-PreMortemXScriptTests.ps1
```

## Validation model

PreMortemX is considered ready only when:

- feature-level acceptance criteria exist
- adversarial evaluator scenarios are defined
- run artifacts are readable and machine-validated
- privacy and permission behavior are documented

## Limitations

- `PreMortemX` currently focuses on release and architecture risk work, not every engineering decision type.
- `PreMortemX` uses local scripts rather than an MCP-backed harness runtime.
- `PreMortemX` does not require AgentFS, though its isolation model informed the design direction.

## V3 Direction

The current v3 direction is:
- structured multi-agent deliberation
- specialist risk agents with orchestrator synthesis
- rationale-backed orchestrator override
- calibration workflows using user-supplied curated datasets

The intended calibration model is explicit:
- dataset quality is the user’s responsibility
- PreMortemX should educate users on what a good calibration dataset looks like
- poor datasets should be treated as a calibration risk, not as trusted truth
