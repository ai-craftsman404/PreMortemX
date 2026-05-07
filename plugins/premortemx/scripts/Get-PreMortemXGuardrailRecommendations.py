from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib.premortemx_registry import guardrail_recommendations, plugin_root_from_script


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ProjectSlug", required=True)
    args = parser.parse_args()
    plugin_root = plugin_root_from_script(Path(__file__))
    print(json.dumps(guardrail_recommendations(plugin_root, args.ProjectSlug), indent=4))


if __name__ == "__main__":
    main()
