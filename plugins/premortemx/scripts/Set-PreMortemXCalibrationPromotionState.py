from __future__ import annotations

import argparse
import json

from lib import premortemx_calibration_store as store


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--CaseId", required=True)
    parser.add_argument("--PromotionState", required=True)
    parser.add_argument("--ChangedBy", required=True)
    parser.add_argument("--Reason", required=True)
    parser.add_argument("--DatabasePath", required=True)
    args = parser.parse_args()
    conn = store.connect(args.DatabasePath)
    try:
        result = store.set_promotion_state(conn, args.CaseId, args.PromotionState, args.ChangedBy, args.Reason)
    finally:
        conn.close()
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
