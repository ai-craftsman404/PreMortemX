import argparse
import json
import os
import sqlite3
from pathlib import Path


def ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def connect(db_path: str) -> sqlite3.Connection:
    ensure_parent(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY,
            task_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            source_run_id TEXT NOT NULL,
            initial_decision TEXT,
            adjudicated_decision TEXT,
            reviewed_outcome TEXT,
            promotion_state TEXT NOT NULL,
            dataset_version TEXT
        );
        CREATE TABLE IF NOT EXISTS case_artifacts (
            artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
            artifact_type TEXT NOT NULL,
            artifact_ref TEXT NOT NULL,
            is_available INTEGER NOT NULL DEFAULT 1,
            provenance_note TEXT
        );
        CREATE TABLE IF NOT EXISTS case_reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
            reviewer TEXT NOT NULL,
            review_date TEXT NOT NULL,
            rationale_summary TEXT,
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS case_labels (
            label_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
            evidence_quality INTEGER,
            risk_severity INTEGER,
            uncertainty_level INTEGER,
            confidence_expected INTEGER,
            policy_band TEXT,
            drift_tag TEXT,
            false_positive_flag INTEGER NOT NULL DEFAULT 0,
            missed_risk_flag INTEGER NOT NULL DEFAULT 0,
            override_used INTEGER NOT NULL DEFAULT 0,
            override_legitimacy TEXT,
            permission_context TEXT,
            input_availability TEXT
        );
        CREATE TABLE IF NOT EXISTS promotion_events (
            promotion_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
            from_state TEXT,
            to_state TEXT NOT NULL,
            changed_at TEXT NOT NULL,
            changed_by TEXT NOT NULL,
            reason TEXT
        );
        CREATE TABLE IF NOT EXISTS calibration_change_requests (
            change_request_id TEXT PRIMARY KEY,
            requested_at TEXT NOT NULL,
            requested_by TEXT NOT NULL,
            change_tier TEXT NOT NULL,
            change_type TEXT NOT NULL,
            proposed_value TEXT,
            reason TEXT,
            status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS calibration_change_approvals (
            approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
            change_request_id TEXT NOT NULL REFERENCES calibration_change_requests(change_request_id) ON DELETE CASCADE,
            approved_at TEXT NOT NULL,
            approved_by TEXT NOT NULL,
            approval_scope TEXT NOT NULL,
            approval_decision TEXT NOT NULL,
            approval_note TEXT
        );
        CREATE TABLE IF NOT EXISTS dataset_versions (
            dataset_version TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            created_by TEXT NOT NULL,
            description TEXT
        );
        """
    )
    conn.commit()


def flatten_artifact_refs(inspected_inputs):
    refs = []
    for artifact_type, values in inspected_inputs.items():
        if isinstance(values, list):
            for value in values:
                refs.append((artifact_type, str(value), 1, None))
    return refs


def import_reviewed_run(conn: sqlite3.Connection, run_record_path: str, quality_log_path: str, promotion_state: str, dataset_version: str):
    record = json.loads(Path(run_record_path).read_text(encoding="utf-8"))
    quality_log = json.loads(Path(quality_log_path).read_text(encoding="utf-8"))
    reviews = quality_log.get("items", [])
    review = next((item for item in reviews if item.get("runId") == record["runId"]), None)
    if review is None:
        raise SystemExit("Reviewed run import requires a matching quality review entry.")

    case_id = record["runId"]
    conn.execute(
        """
        INSERT INTO cases (
            case_id, task_type, created_at, source_run_id, initial_decision, adjudicated_decision,
            reviewed_outcome, promotion_state, dataset_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(case_id) DO UPDATE SET
            task_type=excluded.task_type,
            initial_decision=excluded.initial_decision,
            adjudicated_decision=excluded.adjudicated_decision,
            reviewed_outcome=excluded.reviewed_outcome,
            promotion_state=excluded.promotion_state,
            dataset_version=excluded.dataset_version
        """,
        (
            case_id,
            record.get("taskCategory", "risk-analysis"),
            record["createdAt"],
            record["runId"],
            record.get("decision"),
            record.get("decision"),
            review.get("reviewOutcome"),
            promotion_state,
            dataset_version,
        ),
    )

    conn.execute("DELETE FROM case_artifacts WHERE case_id = ?", (case_id,))
    for artifact_type, artifact_ref, is_available, note in flatten_artifact_refs(record.get("inspectedInputs", {})):
        conn.execute(
            "INSERT INTO case_artifacts (case_id, artifact_type, artifact_ref, is_available, provenance_note) VALUES (?, ?, ?, ?, ?)",
            (case_id, artifact_type, artifact_ref, is_available, note),
        )

    conn.execute("DELETE FROM case_reviews WHERE case_id = ?", (case_id,))
    conn.execute(
        "INSERT INTO case_reviews (case_id, reviewer, review_date, rationale_summary, notes) VALUES (?, ?, ?, ?, ?)",
        (
            case_id,
            review.get("reviewer", "codex"),
            review.get("reviewedAt"),
            "; ".join(review.get("outcomeNotes", [])) or None,
            json.dumps(
                {
                    "falsePositiveNotes": review.get("falsePositiveNotes", []),
                    "missedRiskNotes": review.get("missedRiskNotes", []),
                }
            ),
        ),
    )

    rubric = record.get("deliberation", {}).get("rubric", {})
    conn.execute("DELETE FROM case_labels WHERE case_id = ?", (case_id,))
    conn.execute(
        """
        INSERT INTO case_labels (
            case_id, evidence_quality, risk_severity, uncertainty_level, confidence_expected, policy_band,
            drift_tag, false_positive_flag, missed_risk_flag, override_used, override_legitimacy,
            permission_context, input_availability
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_id,
            rubric.get("evidenceStrength", 3),
            rubric.get("riskSeverity", 3),
            max(1, 6 - int(rubric.get("confidence", 3))),
            rubric.get("confidence", 3),
            "aligned" if int(rubric.get("policyFit", 3)) >= 3 else "watch",
            "stable",
            1 if review.get("reviewOutcome") == "false-positive" else 0,
            1 if review.get("reviewOutcome") == "missed-risk" else 0,
            1 if record.get("override", {}).get("applied") else 0,
            "recorded" if record.get("override", {}).get("applied") else None,
            record.get("approvalMode", "adaptive"),
            record.get("evidenceCoverage", "incomplete"),
        ),
    )

    conn.execute(
        "INSERT INTO promotion_events (case_id, from_state, to_state, changed_at, changed_by, reason) VALUES (?, ?, ?, ?, ?, ?)",
        (case_id, None, promotion_state, review.get("reviewedAt"), review.get("reviewer", "codex"), "initial import from reviewed run"),
    )
    if dataset_version:
        conn.execute(
            "INSERT OR IGNORE INTO dataset_versions (dataset_version, created_at, created_by, description) VALUES (?, ?, ?, ?)",
            (dataset_version, review.get("reviewedAt"), review.get("reviewer", "codex"), "Auto-created from reviewed runs"),
        )
    conn.commit()
    return {"caseId": case_id, "promotionState": promotion_state, "datasetVersion": dataset_version}


def set_promotion_state(conn: sqlite3.Connection, case_id: str, new_state: str, changed_by: str, reason: str):
    row = conn.execute("SELECT promotion_state FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    if row is None:
        raise SystemExit(f"Case not found: {case_id}")
    old_state = row["promotion_state"]
    conn.execute("UPDATE cases SET promotion_state = ? WHERE case_id = ?", (new_state, case_id))
    conn.execute(
        "INSERT INTO promotion_events (case_id, from_state, to_state, changed_at, changed_by, reason) VALUES (?, ?, ?, datetime('now'), ?, ?)",
        (case_id, old_state, new_state, changed_by, reason),
    )
    conn.commit()
    return {"caseId": case_id, "fromState": old_state, "toState": new_state}


def request_change(conn: sqlite3.Connection, change_request_id: str, requested_by: str, change_tier: str, change_type: str, proposed_value: str, reason: str):
    conn.execute(
        """
        INSERT INTO calibration_change_requests (
            change_request_id, requested_at, requested_by, change_tier, change_type, proposed_value, reason, status
        ) VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?)
        """,
        (change_request_id, requested_by, change_tier, change_type, proposed_value, reason, "pending"),
    )
    conn.commit()
    return {"changeRequestId": change_request_id, "status": "pending"}


def approve_change(conn: sqlite3.Connection, change_request_id: str, approved_by: str, approval_scope: str, approval_decision: str, approval_note: str):
    row = conn.execute("SELECT change_request_id FROM calibration_change_requests WHERE change_request_id = ?", (change_request_id,)).fetchone()
    if row is None:
        raise SystemExit(f"Change request not found: {change_request_id}")
    conn.execute(
        """
        INSERT INTO calibration_change_approvals (
            change_request_id, approved_at, approved_by, approval_scope, approval_decision, approval_note
        ) VALUES (?, datetime('now'), ?, ?, ?, ?)
        """,
        (change_request_id, approved_by, approval_scope, approval_decision, approval_note),
    )
    conn.execute(
        "UPDATE calibration_change_requests SET status = ? WHERE change_request_id = ?",
        ("approved" if approval_decision == "approved" else "rejected", change_request_id),
    )
    conn.commit()
    return {"changeRequestId": change_request_id, "status": "approved" if approval_decision == "approved" else "rejected"}


def summary(conn: sqlite3.Connection):
    total_cases = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    by_state_rows = conn.execute("SELECT promotion_state, COUNT(*) AS count FROM cases GROUP BY promotion_state").fetchall()
    by_state = {row["promotion_state"]: row["count"] for row in by_state_rows}
    total_requests = conn.execute("SELECT COUNT(*) FROM calibration_change_requests").fetchone()[0]
    return {"totalCases": total_cases, "byPromotionState": by_state, "totalChangeRequests": total_requests}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--run-record-path")
    parser.add_argument("--quality-log-path")
    parser.add_argument("--promotion-state")
    parser.add_argument("--dataset-version", default="v1")
    parser.add_argument("--case-id")
    parser.add_argument("--changed-by", default="codex")
    parser.add_argument("--reason", default="")
    parser.add_argument("--change-request-id")
    parser.add_argument("--requested-by", default="codex")
    parser.add_argument("--change-tier")
    parser.add_argument("--change-type")
    parser.add_argument("--proposed-value")
    parser.add_argument("--approved-by", default="codex")
    parser.add_argument("--approval-scope")
    parser.add_argument("--approval-decision")
    parser.add_argument("--approval-note", default="")
    args = parser.parse_args()

    conn = connect(args.db_path)
    init_db(conn)

    if args.command == "init-db":
        result = {"dbPath": args.db_path, "initialized": True}
    elif args.command == "import-reviewed-run":
        result = import_reviewed_run(conn, args.run_record_path, args.quality_log_path, args.promotion_state, args.dataset_version)
    elif args.command == "set-promotion-state":
        result = set_promotion_state(conn, args.case_id, args.promotion_state, args.changed_by, args.reason)
    elif args.command == "request-change":
        result = request_change(conn, args.change_request_id, args.requested_by, args.change_tier, args.change_type, args.proposed_value, args.reason)
    elif args.command == "approve-change":
        result = approve_change(conn, args.change_request_id, args.approved_by, args.approval_scope, args.approval_decision, args.approval_note)
    elif args.command == "summary":
        result = summary(conn)
    else:
        raise SystemExit(f"Unsupported command: {args.command}")

    print(json.dumps(result))


if __name__ == "__main__":
    main()
