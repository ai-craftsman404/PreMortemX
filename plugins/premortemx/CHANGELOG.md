# Changelog

## 0.4.0 - 2026-05-07

- moved `PreMortemX` to a Python-first cross-platform runtime contract
- kept the existing PowerShell runtime intact as fallback compatibility
- added Python implementations for core run creation, run-record validation, and orchestrator deliberation
- added Python implementations for registry updates, registry summaries/views, quality reviews, trend summaries, guardrail recommendations, and advisory-boundary reporting
- added Python wrappers around the calibration store flow for initialization, import, summary, promotion-state changes, and approval-controlled calibration changes
- aligned the skill, manifest, testing surface, and public docs to the Python-first `v4` runtime contract
- expanded Python end-to-end validation to the same release-critical behavior shape as the established PowerShell suite

## 0.3.0 - 2026-05-06

- added `v3a` multi-agent deliberation core with orchestrator adjudication and deliberation artifacts
- added rubric-backed override logic with evidence-gated default and severity/policy backstop
- extended the run-record schema with `taskCategory`, `calibrationState`, `executionBoundary`, and `deliberation`
- added `v3b` SQLite-backed calibration storage and reviewed-run promotion flow
- added promotion states for `trusted`, `provisional`, and `excluded`
- added `v3c` calibration change request/approval flow and advisory delegation boundary script
- expanded the script suite to validate `v3a` / `v3b` / `v3c` locally
- refreshed plugin docs, security review, and test matrix for the `v3` product shape

## 0.2.0 - 2026-05-04

- shipped architecture-validation as a supported second mode
- added a registry summary script for stronger local run views
- added materialized registry views for latest-by-project and attention queues
- added local guardrail-memory recommendations based on prior runs
- added quality-review update and trend-summary scripts
- added quality-aware registry summaries and dashboards
- updated run initialization so report titles and task type adapt by mode
- updated plugin docs and examples for the two-mode product shape

## 0.1.0 - 2026-05-04

- initial PreMortemX v1 plugin release
- added release-first Codex plugin manifest and main skill
- added run artifact, schema, and evaluation design package
- added script-backed run initialization, registry update, and run-record validation
- added local script test harness
- added release, security, and testing documentation
