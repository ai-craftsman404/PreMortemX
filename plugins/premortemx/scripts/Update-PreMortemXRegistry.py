from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib.premortemx_registry import append_index_record, plugin_root_from_script


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--RunRecordPath", required=True)
    args = parser.parse_args()
    plugin_root = plugin_root_from_script(Path(__file__))
    print(json.dumps(append_index_record(plugin_root, args.RunRecordPath), indent=4))


if __name__ == "__main__":
    main()
