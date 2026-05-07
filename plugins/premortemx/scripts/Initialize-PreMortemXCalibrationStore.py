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
        store.init_db(conn)
    finally:
        conn.close()
    print(json.dumps({"databasePath": args.DatabasePath, "initialized": True}, indent=4))


if __name__ == "__main__":
    main()
