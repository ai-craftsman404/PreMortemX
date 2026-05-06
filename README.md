# PreMortemX

PreMortemX is a Codex plugin for evidence-backed pre-mortem release gating and architecture validation.

This public repo contains only the standalone plugin package and the minimal local marketplace metadata needed for Codex to discover it.

## What is included

- `.agents/plugins/marketplace.json`
- `plugins/premortemx/.codex-plugin/plugin.json`
- the `premortemx` skill
- the script-based runtime, tests, and calibration helpers
- public-facing docs:
  - plugin README
  - changelog
  - test matrix
  - security review

## Local install

1. Download or clone this repo.
2. Open the repo in Codex.
3. Open the Plugins UI in Codex.
4. Install or enable `PreMortemX`.
5. Invoke it in chat with `$premortemx`.

## Main plugin docs

See [plugins/premortemx/README.md](plugins/premortemx/README.md).
