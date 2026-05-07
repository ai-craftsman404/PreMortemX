from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib.premortemx_registry import plugin_root_from_script, registry_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ProjectSlug")
    parser.add_argument("--Mode", default="all")
    parser.add_argument("--Limit", type=int, default=20)
    args = parser.parse_args()
    plugin_root = plugin_root_from_script(Path(__file__))
    print(json.dumps(registry_summary(plugin_root, args.ProjectSlug, args.Mode, args.Limit), indent=4))


if __name__ == "__main__":
    main()
