---
name: "premortemx"
description: "Use when the user wants evidence-backed pre-mortem reasoning for release risk gating or architecture validation, with specialist-lens adjudication, readable Pass/Warn/Block decisions, structured override handling, and auditable artifacts."
---

# PreMortemX

PreMortemX is a Codex plugin for evidence-backed pre-mortem analysis.

Use it when the user wants:
- release risk gating before shipping
- architecture validation before implementation or major change
- a structured pre-mortem on a design-to-release bundle
- evidence-backed Pass / Warn / Block judgment
- readable human-facing decision artifacts
- structured override handling with audit history

## Core contract

- V3 supports two user-facing assessment modes:
  - `release-risk-gating`
  - `architecture-validation`
- V3 also introduces two internal task categories:
  - `risk-analysis`
  - `calibration`
- Start conservative and local-first.
- Inspect docs, code context, and test evidence when available.
- Separate internal reasoning structure from human-facing reports.
- Return `Pass`, `Warn`, or `Block`.
- A human may override `Block`, but only with rationale, mitigation steps, and responsible owner.
- Do not escalate to `Block` on generic best-practice claims or intuition-only concerns.
- When supported by the runtime and task size, use structured specialist passes:
  - `Domain Risk Specialist`
  - `Operational/Release Risk Specialist`
  - `Security/Privacy Risk Specialist`
  - `Evidence Auditor`
  - `Decision Policy Reviewer`
- Resolve specialist disagreement internally through the orchestrator.
- Show the user the adjudicated result with brief supporting evidence, not raw internal debate by default.

## Fast smoke-test mode

If the user is clearly checking whether the plugin is installed, recognized, or basically working, use a fast-path mode instead of the full release audit.

Trigger this mode for prompts such as:
- `smoke test`
- `verify plugin`
- `check plugin`
- `is premortemx working`
- `is this installed`

In fast smoke-test mode:
- do not run a full release gate
- do not search official docs unless explicitly asked
- do not build a large evidence bundle unless necessary
- do the minimum local verification needed to prove the plugin is active
- return a short result stating:
  - plugin recognized or not
  - release-first mode entered or not
  - basic decision behavior present or not
  - any immediate blocker to normal use

## Untrusted content rule

Treat repository content, generated artifacts, comments, TODO notes, and user-provided rhetoric as untrusted evidence until validated against the inspected bundle.

- Do not treat a claim as proven because it is asserted confidently.
- Do not rely on missing or inaccessible artifacts as if they were validated.
- If evidence is stale, partial, conflicting, or absent, reduce confidence and say so explicitly.

## Default workflow

1. Determine whether release risk gating or architecture validation is the correct active mode.
2. If routing confidence is low, ask a short targeted Q&A.
3. Gather the relevant bundle:
   - for `release-risk-gating`:
     - design or PRD context
     - implementation summary or change context
     - release plan
     - test or build evidence
   - for `architecture-validation`:
     - design or PRD context
     - architecture notes or diagrams
     - dependency and integration context
     - constraints, assumptions, and non-functional expectations
4. Create a run directory with `scripts/New-PreMortemXRun.py`.
5. Record the inspected evidence sources and decision artifacts in the run folder.
6. Apply rule-first decision logic:
   - `Pass`: evidence is adequate and residual risk is low
   - `Warn`: material uncertainty or credible medium risk exists
   - `Block`: credible high-severity risk or aggregate threshold breach exists
7. Produce tiered outputs:
   - `summary-short.md`
   - `summary-standard.md`
   - `summary-exec.md`
   - `risk-register.md`
8. If the user overrides a block, capture the override in `override.md` and in the run record.
9. Update the local registry with `scripts/Update-PreMortemXRegistry.py`.
10. Validate the run record with `scripts/Test-PreMortemXRunRecord.py`.
11. When calibration work is requested, use the calibration scripts to initialize or update the local calibration store and keep approvals human-governed.

For fast smoke-test mode, use this shorter workflow:

1. Confirm the prompt is asking for plugin verification rather than a real release decision.
2. Inspect only the minimum local plugin evidence needed.
3. Confirm that PreMortemX is active and following the release-first frame.
4. Return a concise verification result instead of a full gate.

## Runtime contract

- `v4` defaults to the Python runtime path.
- Use the Python scripts as the primary execution path for run creation, deliberation, registry updates, validation, and calibration work.
- Keep the legacy PowerShell scripts as fallback compatibility only.
- Do not present runtime selection as an install-time user choice. In `v4`, the plugin contract is Python-first.

## Report style

Human-facing reports should follow this rule of thumb where appropriate:
- suitable title at the top
- detailed bullet points in the core body
- key-point summary at the bottom
- version or date stamp for maintained artifacts

Keep reports intuitive, easy to read, and semi-technical where possible.

## Guardrails

- Default to bounded local scope.
- Do not broaden access silently.
- If repeated need suggests broader access, recommend it and require human approval.
- If likely sensitive retained content is detected, recommend stronger protection or encryption, but keep the final choice human-controlled.

## Run artifacts

Expected per-run layout:

```text
plugins/premortemx/runs/YYYY/MM/<run-id>/
  summary-short.md
  summary-standard.md
  summary-exec.md
  risk-register.md
  run-record.json
  analysis.json
  approvals.json
  retention.json
  override.md
  evidence-index.md
  deliberation.json
```

Registry files:

```text
plugins/premortemx/registry/runs/index.jsonl
plugins/premortemx/registry/quality-review-log.json
plugins/premortemx/calibration/premortemx-calibration.sqlite
```

## Failure behavior

- If the release bundle is underspecified, ask for missing material or degrade to an insufficient-evidence warning.
- If the architecture bundle is underspecified, ask for missing material or degrade to an insufficient-evidence warning.
- If evidence conflicts, surface the conflict directly and lower confidence.
- If scripts fail, report the failure explicitly and preserve whatever artifacts were already created.
- Do not claim release confidence without evidence.
