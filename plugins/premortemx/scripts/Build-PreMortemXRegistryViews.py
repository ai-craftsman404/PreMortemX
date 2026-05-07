from __future__ import annotations

import json
from pathlib import Path

from lib.premortemx_registry import build_registry_views, plugin_root_from_script


def main() -> None:
    plugin_root = plugin_root_from_script(Path(__file__))
    print(json.dumps(build_registry_views(plugin_root), indent=4))


if __name__ == "__main__":
    main()
