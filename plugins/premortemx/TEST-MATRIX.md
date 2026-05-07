# PreMortemX Test Matrix

## Scope

This matrix covers the `0.3.0` release, architecture, multi-agent, calibration, and approval-control plugin build.

## Manifest and discovery

- [x] `plugin.json` exists under `.codex-plugin/`
- [x] manifest fields are valid JSON
- [x] `skills` path resolves to `./skills/`
- [x] local marketplace entry points to `./plugins/premortemx`

## Explicit trigger behavior

- [x] `$premortemx` explicit invocation is documented
- [x] skill description clearly targets release-risk pre-mortem use cases
- [x] skill explicitly supports architecture-validation and v3 adjudication guidance
- [x] live Codex install/discovery verification completed
- [x] live `$premortemx` smoke-test invocation produced a release-gating `Block` decision with evidence-backed reasoning

## Wrong-trigger boundaries

These hardening checks are intentionally tracked as follow-up reliability work rather than claimed as complete in the public `0.3.0` release surface:

- generic brainstorming prompt should not force release gating
- generic coding request should not be reframed as a release review without cause

## Script behavior

- [x] `New-PreMortemXRun.ps1` creates run directory and templates
- [x] `Test-PreMortemXRunRecord.ps1` validates required schema fields
- [x] `Invoke-PreMortemXDeliberation.ps1` completes orchestrator-led adjudication
- [x] `Update-PreMortemXRegistry.ps1` appends registry entry
- [x] `Get-PreMortemXRegistrySummary.ps1` summarizes runs by mode and decision
- [x] `Build-PreMortemXRegistryViews.ps1` builds latest-by-project, attention-queue, and dashboard views
- [x] `Get-PreMortemXGuardrailRecommendations.ps1` emits scope recommendations from prior runs
- [x] `Update-PreMortemXQualityReview.ps1` records reviewed outcomes for a run
- [x] `Get-PreMortemXTrendSummary.ps1` summarizes review outcomes over time
- [x] registry summary and dashboard incorporate quality-review outcomes and pending follow-up counts
- [x] invalid decision values fail validation
- [x] architecture-validation mode creates a valid run record and architecture-titled report templates
- [x] calibration store initializes locally
- [x] reviewed runs can be imported into calibration storage
- [x] calibration promotion-state changes are recorded
- [x] calibration change request and approval flow are validated
- [x] advisory delegation boundary output is validated

## Artifact contract

- [x] per-run directory follows `runs/YYYY/MM/<run-id>/`
- [x] run record includes required fields
- [x] summary and register templates are present
- [x] deliberation artifact is present
- [x] registry index is append-only JSONL
- [x] registry summary output reflects mode counts correctly
- [x] materialized registry views are generated successfully

## Adversarial evaluator cases

- [x] false-positive pressure case defined
- [x] false-pass pressure case defined
- [x] weak-evidence bluff case defined
- [x] doc/code conflict case defined
- [x] test-theater case defined
- [x] wrong-trigger case defined
- [x] override accountability case defined
- [x] sensitive-artifact case defined

## Privacy and approvals

- [x] privacy-first retention is documented
- [x] adaptive approvals are documented
- [x] human-controlled encryption recommendation path is documented
- [x] guardrail-memory recommendation behavior is validated
- [x] quality-followup and trend-summary behavior is validated
- [x] quality-aware registry dashboard behavior is validated
- [x] local-only authority and cloud-only advisory boundary are validated

## Local validation commands

```powershell
powershell -NoProfile -File .\plugins\premortemx\scripts\tests\Run-PreMortemXScriptTests.ps1
```
