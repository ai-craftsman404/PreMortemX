# PreMortemX

Evidence-backed pre-mortem risk analysis for Codex, with orchestrated adjudication, governed calibration, and a Python-first cross-platform runtime.

![PreMortemX hero](assets/premortemx-hero.png)

## What it is

PreMortemX brings established risk-assessment discipline into Codex:

- specialist agent-team analysis
- orchestrated adjudication
- evidence-backed `Pass` / `Warn` / `Block` outcomes
- governed run artifacts for review, approvals, and calibration

## 30-second path

1. Open the repo root in Codex.
2. Enable `PreMortemX` in the Plugins UI.
3. Paste this prompt:

```text
$premortemx Validate this architecture and identify the top design risks before implementation.
```

4. Expect:

- a bounded artifact check instead of guessing
- an adjudicated result
- governed artifacts for deeper review

## Real example surface

![Focused previews](assets/premortemx-focused-previews.png)

- [Executive summary](../plugins/premortemx/examples/sample-warn-release/summary-exec.md)
- [Start here](../plugins/premortemx/examples/sample-warn-release/start-here.md)
- [Approvals](../plugins/premortemx/examples/sample-warn-release/approvals.json)
- [Risk register](../plugins/premortemx/examples/sample-warn-release/risk-register.md)

## Visual journey surface

The current `v6a` journey-view artifact turns the agent-team and harness path into a visual story with failed-future framing, rubric-based classification, and richer branch comparison:

![V6A journey surface](assets/premortemx-v6a-journey-showcase-journeyfirst.png)

- [Journey example](../plugins/premortemx/examples/sample-block-journey/README.md)
- [Journey HTML](../plugins/premortemx/examples/sample-block-journey/journey-view.html)
- [Journey JSON](../plugins/premortemx/examples/sample-block-journey/journey-view.json)

## Validated platforms

- Windows
- Linux through the Python runtime path

macOS is reasonably expected through Python, but not yet validated end to end.

## Repo

- [GitHub repository](https://github.com/ai-craftsman404/PreMortemX)
