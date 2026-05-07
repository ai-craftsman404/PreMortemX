from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib import premortemx_calibration_store as store
from lib.premortemx_registry import plugin_root_from_script


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--RunRecordPath", required=True)
    parser.add_argument("--PromotionState", required=True)
    parser.add_argument("--DatasetVersion", default="")
    parser.add_argument("--DatabasePath", required=True)
    args = parser.parse_args()
    plugin_root = plugin_root_from_script(Path(__file__))
    quality_log_path = plugin_root / "registry" / "quality-review-log.json"
    conn = store.connect(args.DatabasePath)
    try:
        result = store.import_reviewed_run(
            conn,
            args.RunRecordPath,
            str(quality_log_path),
            args.PromotionState,
            args.DatasetVersion or None,
        )
    finally:
        conn.close()

    record_path = Path(args.RunRecordPath)
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["calibrationState"]["promotionState"] = args.PromotionState
    record["calibrationState"]["datasetVersion"] = args.DatasetVersion or None
    record["calibrationState"]["caseId"] = result["caseId"]
    record_path.write_text(json.dumps(record, indent=4), encoding="utf-8")
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
