from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def plugin_root_from_script(script_path: str | Path) -> Path:
    return Path(script_path).resolve().parent.parent


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_index(index_path: Path) -> list[dict[str, Any]]:
    if not index_path.exists():
        return []
    items: list[dict[str, Any]] = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            items.append(json.loads(line))
    return items


def write_json(path: Path, payload: Any) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def append_index_record(plugin_root: Path, run_record_path: str | Path) -> dict[str, Any]:
    path = Path(run_record_path)
    if not path.exists():
        raise FileNotFoundError(f"Run record not found: {path}")
    record = json.loads(path.read_text(encoding="utf-8"))
    index_path = plugin_root / "registry" / "runs" / "index.jsonl"
    ensure_parent(index_path)
    quality_log_path = plugin_root / "registry" / "quality-review-log.json"
    index_record = {
        "runId": record["runId"],
        "createdAt": record["createdAt"],
        "updatedAt": record["updatedAt"],
        "projectSlug": record["projectSlug"],
        "mode": record["mode"],
        "taskCategory": record["taskCategory"],
        "decision": record["decision"],
        "confidenceBand": record["confidenceBand"],
        "artifactPath": record["artifactPath"],
        "likelySensitive": record["sensitivityReview"]["likelySensitive"],
        "overrideApplied": record["override"]["applied"],
        "promotionState": record["calibrationState"]["promotionState"],
        "deliberationStatus": record["deliberation"]["status"],
    }
    with index_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(index_record, separators=(",", ":")) + "\n")
    if not quality_log_path.exists():
        write_json(quality_log_path, {"items": []})
    return index_record


def quality_log_items(plugin_root: Path) -> list[dict[str, Any]]:
    return load_json(plugin_root / "registry" / "quality-review-log.json", {"items": []}).get("items", [])


def registry_summary(plugin_root: Path, project_slug: str | None = None, mode: str = "all", limit: int = 20) -> dict[str, Any]:
    items = load_index(plugin_root / "registry" / "runs" / "index.jsonl")
    if project_slug:
        items = [item for item in items if item["projectSlug"] == project_slug]
    if mode != "all":
        items = [item for item in items if item["mode"] == mode]
    sorted_items = sorted(items, key=lambda item: item["createdAt"], reverse=True)
    review_items = quality_log_items(plugin_root)
    if project_slug:
        review_items = [item for item in review_items if item["projectSlug"] == project_slug]
    if mode != "all":
        review_items = [item for item in review_items if item["mode"] == mode]
    reviewed_ids = {item["runId"] for item in review_items}
    return {
        "totalRuns": len(items),
        "byDecision": dict(Counter(item["decision"] for item in items)),
        "byMode": dict(Counter(item["mode"] for item in items)),
        "totalReviewed": len(review_items),
        "pendingQualityFollowup": len([item for item in items if item["runId"] not in reviewed_ids]),
        "byReviewOutcome": dict(Counter(item["reviewOutcome"] for item in review_items)),
        "latestRuns": sorted_items[:limit],
    }


def build_registry_views(plugin_root: Path) -> dict[str, Any]:
    index_items = load_index(plugin_root / "registry" / "runs" / "index.jsonl")
    views_root = plugin_root / "registry" / "views"
    latest_by_project_path = views_root / "latest-by-project.json"
    attention_queue_path = views_root / "attention-queue.json"
    dashboard_path = views_root / "dashboard.md"
    views_root.mkdir(parents=True, exist_ok=True)

    if not index_items:
        write_json(latest_by_project_path, {})
        write_json(attention_queue_path, [])
        dashboard_path.write_text(
            "\n".join(
                [
                    "# PreMortemX Registry Dashboard",
                    "",
                    "- Total runs: 0",
                    "- Attention queue: 0",
                    "",
                    "## Latest By Project",
                    "",
                    "- No runs recorded.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return {"totalRuns": 0, "projects": 0, "attention": 0}

    sorted_items = sorted(index_items, key=lambda item: item["createdAt"], reverse=True)
    latest_by_project: dict[str, dict[str, Any]] = {}
    for item in sorted_items:
        latest_by_project.setdefault(item["projectSlug"], item)

    review_items = quality_log_items(plugin_root)
    reviewed_by_run = {item["runId"]: item for item in review_items}
    attention_queue = [
        item
        for item in sorted_items
        if item["decision"] == "Block" or item["overrideApplied"] is True or item["runId"] not in reviewed_by_run
    ]

    write_json(latest_by_project_path, latest_by_project)
    write_json(attention_queue_path, attention_queue)

    block_count = len([item for item in sorted_items if item["decision"] == "Block"])
    override_count = len([item for item in sorted_items if item["overrideApplied"] is True])
    reviewed_count = len(review_items)
    pending_review_count = len([item for item in sorted_items if item["runId"] not in reviewed_by_run])
    false_positive_count = len([item for item in review_items if item["reviewOutcome"] == "false-positive"])
    missed_risk_count = len([item for item in review_items if item["reviewOutcome"] == "missed-risk"])

    lines = [
        "# PreMortemX Registry Dashboard",
        "",
        f"- Total runs: {len(sorted_items)}",
        f"- Projects tracked: {len(latest_by_project)}",
        f"- Blocks: {block_count}",
        f"- Overrides: {override_count}",
        f"- Reviewed runs: {reviewed_count}",
        f"- Pending quality follow-up: {pending_review_count}",
        f"- False positives logged: {false_positive_count}",
        f"- Missed risks logged: {missed_risk_count}",
        f"- Attention queue: {len(attention_queue)}",
        "",
        "## Latest By Project",
        "",
    ]
    if not latest_by_project:
        lines.append("- No runs recorded.")
    else:
        for project, entry in latest_by_project.items():
            lines.append(f"- {project}: {entry['decision']} [{entry['mode']}] at {entry['createdAt']}")
    dashboard_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"totalRuns": len(sorted_items), "projects": len(latest_by_project), "attention": len(attention_queue)}


def update_quality_review(
    plugin_root: Path,
    run_record_path: str | Path,
    review_outcome: str,
    reviewer: str,
    outcome_notes: str | None = None,
    false_positive_notes: str | None = None,
    missed_risk_notes: str | None = None,
) -> dict[str, Any]:
    path = Path(run_record_path)
    if not path.exists():
        raise FileNotFoundError(f"Run record not found: {path}")
    record = json.loads(path.read_text(encoding="utf-8"))
    quality_log_path = plugin_root / "registry" / "quality-review-log.json"
    log = load_json(quality_log_path, {"items": []})
    items = list(log.get("items", []))
    reviewed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z")
    existing = next((item for item in items if item["runId"] == record["runId"]), None)
    if existing is None:
        existing = {
            "runId": record["runId"],
            "projectSlug": record["projectSlug"],
            "mode": record["mode"],
            "taskCategory": record["taskCategory"],
            "decision": record["decision"],
            "reviewOutcome": review_outcome,
            "reviewer": reviewer,
            "reviewedAt": reviewed_at,
            "outcomeNotes": [],
            "falsePositiveNotes": [],
            "missedRiskNotes": [],
        }
        items.append(existing)
    else:
        existing["reviewOutcome"] = review_outcome
        existing["reviewer"] = reviewer
        existing["reviewedAt"] = reviewed_at
    if outcome_notes:
        existing["outcomeNotes"] = list(existing.get("outcomeNotes", [])) + [outcome_notes]
    if false_positive_notes:
        existing["falsePositiveNotes"] = list(existing.get("falsePositiveNotes", [])) + [false_positive_notes]
    if missed_risk_notes:
        existing["missedRiskNotes"] = list(existing.get("missedRiskNotes", [])) + [missed_risk_notes]
    write_json(quality_log_path, {"items": items})

    qf = record["qualityFollowup"]
    qf["status"] = "reviewed"
    qf["outcomeNotes"] = list(qf.get("outcomeNotes", [])) + list(existing.get("outcomeNotes", []))
    qf["falsePositiveNotes"] = list(qf.get("falsePositiveNotes", [])) + list(existing.get("falsePositiveNotes", []))
    qf["missedRiskNotes"] = list(qf.get("missedRiskNotes", [])) + list(existing.get("missedRiskNotes", []))
    record["updatedAt"] = reviewed_at
    path.write_text(json.dumps(record, indent=4), encoding="utf-8")
    return existing


def trend_summary(plugin_root: Path, project_slug: str | None = None, mode: str = "all") -> dict[str, Any]:
    items = quality_log_items(plugin_root)
    if project_slug:
        items = [item for item in items if item["projectSlug"] == project_slug]
    if mode != "all":
        items = [item for item in items if item["mode"] == mode]
    latest = sorted(items, key=lambda item: item["reviewedAt"], reverse=True)[:20]
    return {
        "totalReviewed": len(items),
        "byOutcome": dict(Counter(item["reviewOutcome"] for item in items)),
        "byMode": dict(Counter(item["mode"] for item in items)),
        "latestReviews": latest,
    }


def advisory_delegation_plan() -> dict[str, Any]:
    return {
        "authorityMode": "local-only",
        "optionallyDelegated": [
            "adversarial critique",
            "narrow specialist review",
            "calibration batch analysis",
        ],
        "neverDelegated": [
            "final decision",
            "final approval",
            "audit writes",
            "permission escalation authority",
        ],
    }


def guardrail_recommendations(plugin_root: Path, project_slug: str) -> dict[str, Any]:
    items = load_index(plugin_root / "registry" / "runs" / "index.jsonl")
    project_items = [item for item in items if item["projectSlug"] == project_slug]
    recommendations: list[str] = []
    reviewed = quality_log_items(plugin_root)
    reviewed_runs = len([item for item in reviewed if item["projectSlug"] == project_slug])
    blocks = len([item for item in project_items if item["decision"] == "Block"])
    if blocks >= 1:
        recommendations.append("Keep release-risk gating enabled by default for this project.")
    if reviewed_runs >= 1:
        recommendations.append("Use prior reviewed runs to keep permission expansion conservative.")
    if not recommendations:
        recommendations.append("No project-specific guardrail expansion is recommended yet.")
    return {
        "projectSlug": project_slug,
        "reviewedRuns": reviewed_runs,
        "recommendations": recommendations,
    }
