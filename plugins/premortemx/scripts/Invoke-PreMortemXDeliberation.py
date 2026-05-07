from __future__ import annotations

import argparse
import json

from lib.premortemx_runtime import invoke_deliberation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--RunRecordPath", required=True)
    parser.add_argument("--SpecialistInputPath")
    args = parser.parse_args()
    print(json.dumps(invoke_deliberation(args.RunRecordPath, args.SpecialistInputPath), indent=4))


if __name__ == "__main__":
    main()
