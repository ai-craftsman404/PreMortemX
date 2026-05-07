from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib.premortemx_registry import plugin_root_from_script, trend_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ProjectSlug")
    parser.add_argument("--Mode", default="all")
    args = parser.parse_args()
    plugin_root = plugin_root_from_script(Path(__file__))
    print(json.dumps(trend_summary(plugin_root, args.ProjectSlug, args.Mode), indent=4))


if __name__ == "__main__":
    main()
