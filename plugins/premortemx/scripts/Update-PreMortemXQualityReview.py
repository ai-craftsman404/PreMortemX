from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib.premortemx_registry import plugin_root_from_script, update_quality_review


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--RunRecordPath", required=True)
    parser.add_argument("--ReviewOutcome", default="unknown")
    parser.add_argument("--Reviewer", default="codex")
    parser.add_argument("--OutcomeNotes")
    parser.add_argument("--FalsePositiveNotes")
    parser.add_argument("--MissedRiskNotes")
    args = parser.parse_args()
    plugin_root = plugin_root_from_script(Path(__file__))
    print(
        json.dumps(
            update_quality_review(
                plugin_root,
                args.RunRecordPath,
                args.ReviewOutcome,
                args.Reviewer,
                args.OutcomeNotes,
                args.FalsePositiveNotes,
                args.MissedRiskNotes,
            ),
            indent=4,
        )
    )


if __name__ == "__main__":
    main()
