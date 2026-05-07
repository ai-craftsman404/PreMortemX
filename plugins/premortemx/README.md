<div align="center">

# PreMortemX

### Evidence-backed pre-mortem risk analysis for Codex, with orchestrated adjudication and governed calibration.

[![Version](https://img.shields.io/badge/version-0.3.0-8C3B2F?style=flat-square)](.codex-plugin/plugin.json)
[![Codex Plugin](https://img.shields.io/badge/Codex-Plugin-8C3B2F?style=flat-square)](.codex-plugin/plugin.json)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

[**Quick Start**](#quick-start) · [**How It Works**](#how-it-works) · [**Capabilities**](#capabilities) · [**Testing**](#testing)

</div>

---

## The Problem

Engineering teams already know how to do risk assessment, but the process is usually slow, inconsistent, and hard to maintain. Important risks get missed, weak concerns get over-weighted, and decision records are often too thin to be useful later.

**PreMortemX applies established risk-assessment practice through an AI operating model.** It uses specialist risk lenses, orchestrated adjudication, evidence-backed outputs, and calibration-ready records so teams can make faster decisions without abandoning disciplined governance.

---

## Why PreMortemX

- applies familiar risk-assessment discipline instead of inventing a new methodology
- uses specialist AI lenses instead of a single generic analysis pass
- resolves internal disagreement through orchestrated adjudication
- keeps final output readable, concise, and evidence-backed
- supports calibration and governance over time through reviewed signals

The novelty is the AI operating model, not the underlying risk principles.

### What makes it different

`PreMortemX` is not just a guided pre-mortem prompt.

Unlike lighter pre-mortem skills that mainly structure brainstorming, `PreMortemX` is designed as a governed decision-support system:
- specialist risk lenses instead of one undifferentiated pass
- an agent team with orchestrated adjudication instead of naive vote counting
- evidence-backed decisions instead of intuition-heavy output
- structured approvals and overrides instead of silent judgment shifts
- calibration from reviewed cases instead of learning blindly from raw history

That distinction matters most in regulated or higher-accountability environments where teams need discipline, traceability, and repeatable governance rather than a clever prompt alone.

### Risk-governance principles carried into the design

PreMortemX was deliberately shaped around established risk-assessment and governance practices, including:
- evidence-first judgment
- explicit adjudication and accountability
- severity, uncertainty, and confidence treated as separate signals
- conservative handling of incomplete evidence
- human-governed escalation and override paths
- auditability of decisions, approvals, and later calibration changes

These practices are the north star. The AI layer is how they are operationalized inside Codex.

### Why these specialist roles exist

The agent team was deliberately shaped to simulate the kinds of roles found in real-world risk assessment and governance processes.

Instead of one generic model trying to do everything, `PreMortemX` uses specialist roles that mirror how an actual risk team separates concerns:
- domain and implementation risk
- operational and release risk
- security and privacy risk
- evidence review
- policy and decision review
- final adjudication by the orchestrator

That makes the system more than a prompt pattern. It is an AI translation of a real assessment-team structure.

---

## Quick Start

### 1. Open the plugin package in Codex

Codex should discover the plugin from the local marketplace metadata in this repo.

### 2. Install or enable `PreMortemX`

Use the Codex Plugins UI to install and enable the plugin.

### 3. Run the smoke test first

```text
$premortemx Smoke test this plugin and confirm it is active.
```

### 4. Run a real assessment prompt

```text
$premortemx Run a pre-mortem on this release plan and tell me whether we should ship.
```

```text
$premortemx Validate this architecture and identify the top design risks before implementation.
```

### 5. If discovery fails

- open the repo root, not only the nested plugin folder
- confirm local marketplace metadata is present at `.agents/plugins/marketplace.json`
- reopen the repo root in Codex and check the Plugins UI again

### 6. Run the local test suite

```powershell
powershell -NoProfile -File .\plugins\premortemx\scripts\tests\Run-PreMortemXScriptTests.ps1
```

---

## How It Works

| Step | What happens |
|------|-------------|
| **1. Route** | `PreMortemX` determines whether release-risk gating or architecture validation is the right mode |
| **2. Inspect** | It gathers docs, code context, tests, and supporting artifacts available in the local bundle |
| **3. Deliberate** | Specialist risk lenses assess the case and the orchestrator adjudicates the result |
| **4. Decide** | The plugin returns `Pass`, `Warn`, or `Block` with concise supporting evidence |
| **5. Record** | Run artifacts, registry updates, and optional quality review data are written locally |
| **6. Calibrate** | Reviewed runs can be promoted into a governed calibration dataset over time |

By design, the user sees the adjudicated outcome rather than raw internal debate.

---

## Capabilities

### Core assessment modes

- `release-risk-gating`
- `architecture-validation`

### V3 highlights

- multi-agent deliberation with orchestrator adjudication
- rubric-backed override logic with internal `1-5` grading
- adjudicated user output instead of exposed internal debate
- SQLite-backed calibration dataset store
- reviewed-run promotion states: `trusted`, `provisional`, `excluded`
- calibration change requests and approvals
- local-only authority with optional cloud-advisory edges
- fully usable in local-first mode with no required external API dependency

### Roadmap

- `v1`: release-first pre-mortem gating with structured artifacts and overrides
- `v2`: architecture validation, stronger registry views, quality follow-up, and trend summaries
- `v3`: multi-agent adjudication, governed calibration, reviewed-run promotion, and approval-controlled change flows

### Decision model

- `Pass`: adequate evidence, low residual risk, no warn/block rule triggered
- `Warn`: meaningful uncertainty or credible medium risk
- `Block`: credible high-severity risk or aggregate threshold breach

A `Block` may be overridden by a human, but the override must preserve:
- rationale
- mitigation steps
- responsible owner

---

## Project Structure

```text
plugins/premortemx/
  .codex-plugin/plugin.json
  skills/
  scripts/
  registry/
  runs/
  calibration/
```

### Key scripts

- `New-PreMortemXRun.ps1`
- `Invoke-PreMortemXDeliberation.ps1`
- `Test-PreMortemXRunRecord.ps1`
- `Update-PreMortemXRegistry.ps1`
- `Update-PreMortemXQualityReview.ps1`
- `Initialize-PreMortemXCalibrationStore.ps1`
- `Import-PreMortemXReviewedRunToCalibration.ps1`
- `Request-PreMortemXCalibrationChange.ps1`
- `Approve-PreMortemXCalibrationChange.ps1`

### Key artifacts

- `run-record.json`
- `analysis.json`
- `deliberation.json`
- `summary-short.md`
- `summary-standard.md`
- `summary-exec.md`
- `risk-register.md`

---

## Testing

Current local validation covers:

- run initialization
- schema validation
- orchestrator deliberation
- registry updates and dashboards
- quality review logging
- calibration store initialization
- reviewed-run import and promotion flow
- calibration change requests and approvals
- advisory-boundary reporting

Primary test entrypoint:

```powershell
powershell -NoProfile -File .\plugins\premortemx\scripts\tests\Run-PreMortemXScriptTests.ps1
```

Related public docs:

- [CHANGELOG.md](CHANGELOG.md)
- [TEST-MATRIX.md](TEST-MATRIX.md)
- [SECURITY-REVIEW.md](SECURITY-REVIEW.md)

---

## Limitations

- `PreMortemX` currently focuses on release and architecture risk work, not every engineering decision type
- it uses local scripts rather than an MCP-backed runtime
- optional cloud-advisory behavior is intentionally non-authoritative
- calibration quality depends on user-curated reviewed data

---

## License

[MIT](LICENSE)
