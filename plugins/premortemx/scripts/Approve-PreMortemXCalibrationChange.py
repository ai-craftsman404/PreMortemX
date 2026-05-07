from __future__ import annotations

import argparse
import json

from lib import premortemx_calibration_store as store


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ChangeRequestId", required=True)
    parser.add_argument("--ApprovalScope", required=True)
    parser.add_argument("--ApprovalDecision", required=True)
    parser.add_argument("--ApprovedBy", required=True)
    parser.add_argument("--ApprovalNote", required=True)
    parser.add_argument("--DatabasePath", required=True)
    args = parser.parse_args()
    conn = store.connect(args.DatabasePath)
    try:
        result = store.approve_change(
            conn,
            args.ChangeRequestId,
            args.ApprovedBy,
            args.ApprovalScope,
            args.ApprovalDecision,
            args.ApprovalNote,
        )
    finally:
        conn.close()
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
