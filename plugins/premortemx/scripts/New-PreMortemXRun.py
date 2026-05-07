from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib.premortemx_runtime import create_run, plugin_root_from_script


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ProjectSlug", required=True)
    parser.add_argument("--Mode", default="release-risk-gating")
    parser.add_argument("--Decision", default="Warn")
    parser.add_argument("--ConfidenceBand", default="Medium")
    args = parser.parse_args()

    plugin_root = plugin_root_from_script(Path(__file__))
    payload = create_run(
        plugin_root=plugin_root,
        project_slug=args.ProjectSlug,
        mode=args.Mode,
        decision=args.Decision,
        confidence_band_value=args.ConfidenceBand,
    )
    print(json.dumps(payload, indent=4))


if __name__ == "__main__":
    main()
