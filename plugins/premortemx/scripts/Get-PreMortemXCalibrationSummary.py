from __future__ import annotations

import argparse
import json

from lib import premortemx_calibration_store as store


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--DatabasePath", required=True)
    args = parser.parse_args()
    conn = store.connect(args.DatabasePath)
    try:
        total_cases = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        rows = conn.execute("SELECT promotion_state, COUNT(*) AS count FROM cases GROUP BY promotion_state").fetchall()
        by_state = {row["promotion_state"]: row["count"] for row in rows}
    finally:
        conn.close()
    print(json.dumps({"totalCases": total_cases, "byPromotionState": by_state}, indent=4))


if __name__ == "__main__":
    main()
