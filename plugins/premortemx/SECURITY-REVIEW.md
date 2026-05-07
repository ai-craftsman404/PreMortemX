# PreMortemX Security And Privacy Review

## Release

- Version: `0.4.0`
- Date: `2026-05-07`

## Security posture

- local-first plugin design
- no mandatory external APIs
- no built-in network calls
- conservative default scope
- broader access requires human approval

## Sensitive-data posture

- likely sensitive retained content should be identified and flagged
- stronger protection or encryption can be recommended
- final retention/protection choice remains human-controlled
- summaries should avoid unnecessary reproduction of sensitive source content

## Filesystem posture

- run artifacts remain under `plugins/premortemx/runs/`
- registry state remains under `plugins/premortemx/registry/`
- no destructive filesystem actions are built into the runtime scripts
- calibration storage is local SQLite under the plugin directory

## Script review

### `New-PreMortemXRun.py`

- primary `v4` run-initialization path
- creates local run directories and template artifacts
- writes only under the plugin’s own directories
- no network dependency

### `Invoke-PreMortemXDeliberation.py`

- primary `v4` orchestrator adjudication path
- records specialist-lens findings and orchestrator adjudication locally
- no network dependency
- preserves human escalation when uncertainty and sensitivity remain high

### `Update-PreMortemXRegistry.py`

- primary `v4` registry-update path
- appends local metadata to JSONL registry index
- does not broaden scope or exfiltrate data

### `Test-PreMortemXRunRecord.py`

- primary `v4` validation path
- validates local run-record structure only
- no side effects beyond reading the specified record

### Legacy PowerShell fallback

### `New-PreMortemXRun.ps1`

- creates local run directories and template artifacts
- writes only under the plugin’s own directories
- no external process launch beyond normal PowerShell execution

### `Invoke-PreMortemXDeliberation.ps1`

- records specialist-lens findings and orchestrator adjudication locally
- no external process launch or network dependency
- preserves human escalation when uncertainty and sensitivity remain high

### `Update-PreMortemXRegistry.ps1`

- appends local metadata to JSONL registry index
- does not broaden scope or exfiltrate data

### `Test-PreMortemXRunRecord.ps1`

- validates local run-record structure only
- no side effects beyond reading the specified record

### Calibration scripts

- initialize and update only the local SQLite calibration store
- require reviewed runs for promotion into calibration data
- keep approval handling explicit and locally recorded
- do not grant cloud or remote authority over final decisions

## Prompt and reasoning risks

- false confidence on weak evidence
- generic best-practice filler risks
- implicit mode hijacking on unrelated prompts
- privacy leakage into summaries

Mitigations:

- rule-first decision model
- adversarial evaluator scenarios
- trigger discipline in skill contract
- privacy-first report guidance

## Residual risks

- v3 does not automate content redaction
- v3 does not enforce encryption technically; it recommends based on sensitivity context
- optional cloud-advisory paths are not implemented as authoritative execution
- implicit trigger quality still depends on Codex runtime behavior and user context

## Conclusion

PreMortemX `0.4.0` is acceptable for local-first release and architecture risk use with a Python-first cross-platform runtime, governed calibration workflows, and PowerShell fallback compatibility, provided the documented privacy, approval, and evaluator guidance are followed and the plugin is not misrepresented as a fully autonomous release authority.
