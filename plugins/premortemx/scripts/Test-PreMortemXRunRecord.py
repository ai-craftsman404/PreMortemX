from __future__ import annotations

import argparse
import json

from lib.premortemx_runtime import validate_run_record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--RunRecordPath", required=True)
    args = parser.parse_args()
    print(json.dumps(validate_run_record(args.RunRecordPath), indent=4))


if __name__ == "__main__":
    main()
