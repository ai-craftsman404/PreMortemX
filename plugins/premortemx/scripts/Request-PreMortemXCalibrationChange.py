from __future__ import annotations

import argparse
import json
import uuid

from lib import premortemx_calibration_store as store


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ChangeTier", required=True)
    parser.add_argument("--ChangeType", required=True)
    parser.add_argument("--ProposedValue", required=True)
    parser.add_argument("--Reason", required=True)
    parser.add_argument("--RequestedBy", required=True)
    parser.add_argument("--DatabasePath", required=True)
    args = parser.parse_args()
    conn = store.connect(args.DatabasePath)
    try:
        result = store.request_change(
            conn,
            f"pmx-change-{uuid.uuid4().hex[:8]}",
            args.RequestedBy,
            args.ChangeTier,
            args.ChangeType,
            args.ProposedValue,
            args.Reason,
        )
    finally:
        conn.close()
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
