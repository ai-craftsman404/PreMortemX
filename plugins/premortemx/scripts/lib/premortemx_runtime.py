from __future__ import annotations

import json
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_DECISIONS = {"Pass", "Warn", "Block"}
ALLOWED_MODES = {"release-risk-gating", "architecture-validation"}
ALLOWED_TASK_CATEGORIES = {"risk-analysis", "calibration"}
ALLOWED_PROMOTION_STATES = {"trusted", "provisional", "excluded"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def run_id(project_slug: str, now: datetime) -> str:
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:6]
    return f"pmx-{project_slug}-{stamp}-{suffix}"


def confidence_to_int(band: str) -> int:
    mapping = {
        "Very Low": 1,
        "Low": 2,
        "Medium": 3,
        "Medium-High": 4,
        "High": 4,
        "Very High": 5,
    }
    return mapping.get(band, 3)


def confidence_band(value: int) -> str:
    bands = {
        1: "Very Low",
        2: "Low",
        3: "Medium",
        4: "Medium-High",
        5: "High",
    }
    return bands[max(1, min(5, int(value)))]


def decision_rank(decision: str) -> int:
    return {"Pass": 1, "Warn": 2, "Block": 3}[decision]


def plugin_root_from_script(script_path: str | Path) -> Path:
    return Path(script_path).resolve().parent.parent


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def report_title(mode: str) -> str:
    return (
        "PreMortemX Architecture Assessment"
        if mode == "architecture-validation"
        else "PreMortemX Release Assessment"
    )


def task_type_for_mode(mode: str) -> str:
    return "architecture-review" if mode == "architecture-validation" else "premortem"


def default_record(
    project_slug: str,
    mode: str,
    decision: str,
    confidence_band_value: str,
    now: datetime,
    run_dir: Path,
) -> dict[str, Any]:
    rid = run_id(project_slug, now)
    artifact_rel = run_dir.as_posix().split("/plugins/premortemx/")[-1] if "/plugins/premortemx/" in run_dir.as_posix() else "/".join(run_dir.parts[-4:])
    record = {
        "schemaVersion": "1.0",
        "runId": rid,
        "pluginVersion": "0.3.0",
        "createdAt": now.isoformat().replace("+00:00", "Z"),
        "updatedAt": now.isoformat().replace("+00:00", "Z"),
        "status": "initialized",
        "projectSlug": project_slug,
        "taskType": task_type_for_mode(mode),
        "taskCategory": "risk-analysis",
        "initiator": "codex",
        "executionMode": "skill+scripts",
        "approvalMode": "adaptive",
        "privacyMode": "privacy-first-hybrid",
        "retentionClass": "standard",
        "artifactPath": artifact_rel.replace("\\", "/"),
        "registryRefs": {"indexKey": f"{now.strftime('%Y-%m')}/{rid}"},
        "inputFingerprint": {"contextHash": None, "promptHash": None},
        "mode": mode,
        "routingType": "hybrid",
        "decision": decision,
        "confidenceBand": confidence_band_value,
        "inspectedInputs": {
            "designDocs": [],
            "architectureContext": [],
            "implementationContext": [],
            "releasePlan": [],
            "testEvidence": [],
            "dependencies": [],
            "constraints": [],
        },
        "riskSummary": {"low": 0, "medium": 0, "high": 0},
        "topRisks": [],
        "evidenceCoverage": "incomplete",
        "calibrationState": {
            "promotionState": "excluded",
            "datasetVersion": None,
            "caseId": None,
        },
        "executionBoundary": {
            "authorityMode": "local-only",
            "advisoryMode": "cloud-only-advisory",
            "advisoryDelegationAllowed": True,
            "advisoryDelegationUsed": [],
        },
        "deliberation": {
            "version": "3.0",
            "adjudicatedBy": "orchestrator",
            "status": "initialized",
            "sharedRoles": [
                "Evidence Auditor",
                "Decision Policy Reviewer",
                "Orchestrator",
            ],
            "specialistRoles": [
                "Domain Risk Specialist",
                "Operational/Release Risk Specialist",
                "Security/Privacy Risk Specialist",
            ],
            "specialists": [],
            "agreement": {
                "consensusDecision": decision,
                "disagreementLevel": 1,
                "summary": "Pending deliberation.",
            },
            "rubric": {
                "gradingScale": "1-5",
                "confidence": confidence_to_int(confidence_band_value),
                "evidenceStrength": 3,
                "riskSeverity": 3,
                "evidenceCompleteness": 3,
                "disagreementLevel": 1,
                "policyFit": 3,
                "decisionSensitivity": 3,
                "sourceProvenance": 3,
                "mitigationReadiness": 3,
                "calibratedPatternFit": 3,
                "contradictoryArtifactPressure": 1,
            },
            "overrideModel": {
                "defaultTrigger": "evidence-gated",
                "backstopTrigger": "severity-and-policy",
                "overrideApplied": False,
                "overrideReason": None,
                "humanEscalationRequired": False,
                "humanEscalationReasons": [],
                "overrideTestSummary": "Pending override evaluation.",
            },
            "adjudication": {
                "finalDecision": decision,
                "finalConfidenceBand": confidence_band_value,
                "summary": "Pending orchestrator synthesis.",
                "supportingEvidence": [],
                "decisionOwner": None,
                "ruleTriggered": "pending",
                "humanEscalationConsidered": False,
                "residualRiskAfterMitigation": "pending",
                "decisionPath": [],
                "uncertaintyDrivers": [],
            },
        },
        "warnReasons": [],
        "blockReasons": [],
        "outputTiers": ["short", "standard", "exec"],
        "permissionEscalationsRequested": [],
        "permissionEscalationsApproved": [],
        "guardrailRecommendations": [],
        "override": {
            "applied": False,
            "rationale": None,
            "mitigationSteps": [],
            "responsibleOwner": None,
        },
        "sensitivityReview": {
            "likelySensitive": False,
            "recommendedProtection": "none",
            "encryptionUsed": False,
        },
        "artifacts": {
            "summaryShort": "summary-short.md",
            "summaryStandard": "summary-standard.md",
            "summaryExec": "summary-exec.md",
            "riskRegister": "risk-register.md",
            "runRecord": "run-record.json",
            "analysis": "analysis.json",
            "approvals": "approvals.json",
            "retention": "retention.json",
            "override": None,
            "evidenceIndex": "evidence-index.md",
            "deliberation": "deliberation.json",
        },
        "qualityFollowup": {
            "status": "pending",
            "reviewDue": None,
            "falsePositiveNotes": [],
            "missedRiskNotes": [],
            "outcomeNotes": [],
        },
    }
    return record


def _write(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.write_text(json.dumps(payload, indent=4), encoding="utf-8")


def _scaffold_markdown(record: dict[str, Any], mode: str, now_text: str) -> dict[str, str]:
    title = report_title(mode)
    rid = record["runId"]
    decision = record["decision"]
    confidence = record["confidenceBand"]
    return {
        "summary-short.md": "\n".join(
            [
                f"# {title}",
                "",
                f"- Run ID: {rid}",
                f"- Created: {now_text}",
                f"- Updated: {now_text}",
                f"- Mode: {mode}",
                f"- Recommendation: {decision}",
                f"- Confidence: {confidence}",
                "",
                "## Recommendation Snapshot",
                "",
                "- Add the shortest possible decision statement here.",
                "",
                "## Assessment Scope",
                "",
                "- Record what artifact bundle and decision horizon were assessed.",
                "",
                "## Top Concerns",
                "",
                "- Add evidence-backed bullets here.",
                "",
                "## Key Point Summary",
                "",
                "- Keep this section short and easy to scan.",
            ]
        ),
        "summary-standard.md": "\n".join(
            [
                f"# {title}",
                "",
                f"- Run ID: {rid}",
                f"- Created: {now_text}",
                f"- Updated: {now_text}",
                f"- Mode: {mode}",
                f"- Recommendation: {decision}",
                f"- Confidence: {confidence}",
                "",
                "## Recommendation Snapshot",
                "",
                "- Add the top-line judgment here.",
                "",
                "## Assessment Scope And Decision Window",
                "",
                "- Record the inspected artifact boundary and the decision horizon.",
                "",
                "## Decision Owner And Required Action",
                "",
                "- Record who must accept, escalate, or delay the decision.",
                "",
                "## Top Blockers Or Concerns",
                "",
                "- Add detailed bullet points here.",
                "",
                "## Mitigation Path",
                "",
                "- Add recommended mitigation steps here.",
                "",
                "## Confidence And Evidence Note",
                "",
                "- Explain evidence quality and any important uncertainty.",
                "",
                "## Residual Risk Note",
                "",
                "- Explain the expected residual risk if the listed mitigations are completed.",
                "",
                "## Key Point Summary",
                "",
                "- End with the shortest possible decision summary.",
            ]
        ),
        "summary-exec.md": "\n".join(
            [
                f"# {title}",
                "",
                f"- Run ID: {rid}",
                f"- Created: {now_text}",
                f"- Recommendation: {decision}",
                f"- Confidence: {confidence}",
                "",
                "## Architecture Recommendation" if mode == "architecture-validation" else "## Release Recommendation",
                "",
                "- Add the executive-facing architecture recommendation here." if mode == "architecture-validation" else "- Add the executive-facing release recommendation here.",
                "",
                "## Decision Required",
                "",
                "- Record who must accept, escalate, or defer the decision.",
                "",
                "## Top Blockers",
                "",
                "- Add the most important blockers or concerns here.",
                "",
                "## Mitigation Path",
                "",
                "- Add the executive-facing mitigation path here.",
                "",
                "## Proceed Conditions",
                "",
                "- Record what must be true before proceeding.",
                "",
                "## Residual Risk If Proceeding",
                "",
                "- Summarize the expected residual risk after mitigations.",
                "",
                "## Key Point Summary",
                "",
                "- Keep this section brief.",
            ]
        ),
        "risk-register.md": "\n".join(
            [
                "# PreMortemX Architecture Risk Register" if mode == "architecture-validation" else "# PreMortemX Risk Register",
                "",
                f"- Run ID: {rid}",
                f"- Created: {now_text}",
                "",
                "## Scope Reviewed",
                "",
                "- List the inspected design, architecture, code, release, and test artifacts.",
                "",
                "## Detailed Risks",
                "",
                "- `R-01`",
                "  Cause-event-impact: because X, Y may happen, leading to Z impact.",
                "  Likelihood: ``",
                "  Impact: ``",
                "  Current risk: ``",
                "  Residual risk after mitigation: ``",
                "  Response: ``",
                "  Risk owner: ``",
                "  Treatment owner: ``",
                "  Status: ``",
                "  Review date: ``",
                "  Evidence refs: ``",
                "",
                "## Evidence References",
                "",
                "- `EV-01`: artifact, section, freshness, and trust note.",
                "",
                "## Mitigations",
                "",
                "- `R-01`: add mitigation actions here.",
                "",
                "## Unresolved Assumptions",
                "",
                "- Record material uncertainty here.",
                "",
                "## Key Point Summary",
                "",
                "- Keep this section brief and scannable.",
            ]
        ),
        "evidence-index.md": "\n".join(
            [
                "# Evidence Index",
                "",
                f"- Run ID: {rid}",
                "",
                "## Sources",
                "",
                "- `EV-01` | evidence type | artifact | owner/source | freshness | trust level | supports finding IDs | direct / inferred / missing",
            ]
        ),
    }


def create_run(
    plugin_root: str | Path,
    project_slug: str,
    mode: str = "release-risk-gating",
    decision: str = "Warn",
    confidence_band_value: str = "Medium",
) -> dict[str, Any]:
    if mode not in ALLOWED_MODES:
        raise ValueError(f"Invalid mode: {mode}")
    if decision not in ALLOWED_DECISIONS:
        raise ValueError(f"Invalid decision: {decision}")
    root = Path(plugin_root)
    now = utc_now()
    rid = run_id(project_slug, now)
    run_dir = root / "runs" / now.strftime("%Y") / now.strftime("%m") / rid
    ensure_dir(run_dir)

    record = default_record(project_slug, mode, decision, confidence_band_value, now, run_dir)
    record["runId"] = rid
    record["registryRefs"]["indexKey"] = f"{now.strftime('%Y-%m')}/{rid}"
    record["artifactPath"] = f"runs/{now.strftime('%Y')}/{now.strftime('%m')}/{rid}"

    _write_json(run_dir / "run-record.json", record)
    now_text = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    for name, content in _scaffold_markdown(record, mode, now_text).items():
        _write(run_dir / name, content)

    _write_json(
        run_dir / "analysis.json",
        {
            "generatedAt": record["createdAt"],
            "notes": [
                "Structured internal analysis output belongs here.",
                "Keep machine-oriented reasoning concise and auditable.",
            ],
            "decisionContext": {
                "decisionOwner": None,
                "decisionWindow": None,
                "scopeBoundary": None,
                "recommendedAction": None,
            },
            "findings": [
                {
                    "id": "R-01",
                    "title": "Add concise finding title here.",
                    "likelihood": None,
                    "impact": None,
                    "currentRisk": None,
                    "residualRisk": None,
                    "evidenceStrength": None,
                    "response": None,
                    "riskOwner": None,
                    "treatmentOwner": None,
                    "reviewDate": None,
                    "evidenceRefs": [],
                    "summary": "Add concise machine-readable finding summary here.",
                }
            ],
        },
    )
    _write_json(run_dir / "deliberation.json", record["deliberation"])
    _write_json(
        run_dir / "approvals.json",
        {
            "approvalsRequested": [],
            "approvalsGranted": [],
            "recommendation": "stay-conservative",
            "notes": ["Permission escalation events belong here."],
        },
    )
    _write_json(
        run_dir / "retention.json",
        {
            "likelySensitive": False,
            "recommendation": "none",
            "encryptionDecision": "not-requested",
            "notes": ["Retention and sensitivity decisions belong here."],
        },
    )
    quality_log_path = root / "registry" / "quality-review-log.json"
    ensure_dir(quality_log_path.parent)
    if not quality_log_path.exists():
        _write_json(quality_log_path, {"items": []})

    return {
        "RunId": rid,
        "RunPath": str(run_dir),
        "RecordPath": str(run_dir / "run-record.json"),
    }


def _require_fields(record: dict[str, Any], fields: list[str]) -> None:
    for field in fields:
        if field not in record:
            raise ValueError(f"Missing required field '{field}' in run record.")


def validate_run_record(run_record_path: str | Path) -> dict[str, Any]:
    path = Path(run_record_path)
    if not path.exists():
        raise FileNotFoundError(f"Run record not found: {path}")
    record = json.loads(path.read_text(encoding="utf-8"))
    _require_fields(
        record,
        [
            "schemaVersion", "runId", "pluginVersion", "createdAt", "updatedAt", "status",
            "projectSlug", "taskType", "taskCategory", "executionMode", "approvalMode",
            "privacyMode", "retentionClass", "artifactPath", "registryRefs",
            "inputFingerprint", "mode", "decision", "confidenceBand", "inspectedInputs",
            "riskSummary", "calibrationState", "executionBoundary", "deliberation",
            "outputTiers", "permissionEscalationsRequested", "permissionEscalationsApproved",
            "guardrailRecommendations", "override", "sensitivityReview", "artifacts",
            "qualityFollowup",
        ],
    )
    if not re.match(r"^pmx-[a-z0-9\-]+-\d{8}T\d{6}Z-[a-z0-9]{6}$", record["runId"]):
        raise ValueError(f"Run ID format is invalid: {record['runId']}")
    if record["decision"] not in ALLOWED_DECISIONS:
        raise ValueError("Decision must be one of: Pass, Warn, Block")
    if record["mode"] not in ALLOWED_MODES:
        raise ValueError("Mode must be one of: release-risk-gating, architecture-validation")
    if record["taskCategory"] not in ALLOWED_TASK_CATEGORIES:
        raise ValueError("Task category must be one of: risk-analysis, calibration")
    _require_fields(
        record["artifacts"],
        ["summaryShort", "summaryStandard", "summaryExec", "riskRegister", "runRecord", "analysis", "approvals", "retention", "evidenceIndex", "deliberation"],
    )
    rubric = record["deliberation"]["rubric"]
    if rubric["gradingScale"] != "1-5":
        raise ValueError("Deliberation rubric grading scale must be '1-5'.")
    for field in ["confidence", "evidenceStrength", "riskSeverity", "evidenceCompleteness", "disagreementLevel", "policyFit", "decisionSensitivity"]:
        value = int(rubric[field])
        if value < 1 or value > 5:
            raise ValueError(f"Rubric field '{field}' must be within 1-5.")
    if record["calibrationState"]["promotionState"] not in ALLOWED_PROMOTION_STATES:
        raise ValueError("Promotion state must be one of: trusted, provisional, excluded")
    return {"Valid": True, "RunId": record["runId"], "Decision": record["decision"]}


def _new_default_specialist(role: str, decision: str) -> dict[str, Any]:
    return {
        "role": role,
        "recommendation": decision,
        "summary": f"{role} found no additional concerns beyond the current {decision} posture.",
        "evidenceRefs": [],
        "rubric": {
            "confidence": 3,
            "evidenceStrength": 3,
            "riskSeverity": 3,
            "evidenceCompleteness": 3,
            "disagreementLevel": 1,
            "policyFit": 3,
            "decisionSensitivity": 3,
        },
    }


def invoke_deliberation(run_record_path: str | Path, specialist_input_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(run_record_path)
    record = json.loads(path.read_text(encoding="utf-8"))
    run_dir = path.parent
    specialists: list[dict[str, Any]] = []

    if specialist_input_path:
        payload = json.loads(Path(specialist_input_path).read_text(encoding="utf-8"))
        specialists = list(payload.get("specialists", []))
        if payload.get("specialists") is None:
            raise ValueError("Specialist input must contain a 'specialists' array.")
    else:
        for role in record["deliberation"]["specialistRoles"]:
            specialists.append(_new_default_specialist(role, record["decision"]))

    if not specialists:
        raise ValueError("At least one specialist finding is required.")

    decision_groups = Counter(spec["recommendation"] for spec in specialists)
    consensus_decision = sorted(decision_groups.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    consensus_group = [s for s in specialists if s["recommendation"] == consensus_decision]
    minority_views = [s for s in specialists if s["recommendation"] != consensus_decision]

    def avg(field: str, specs: list[dict[str, Any]]) -> int:
        return round(sum(int(s["rubric"][field]) for s in specs) / len(specs))

    consensus_evidence_strength = avg("evidenceStrength", consensus_group)
    all_evidence_completeness = [int(s["rubric"]["evidenceCompleteness"]) for s in specialists]
    all_confidence = [int(s["rubric"]["confidence"]) for s in specialists]
    all_severity = [int(s["rubric"]["riskSeverity"]) for s in specialists]
    all_policy_fit = [int(s["rubric"]["policyFit"]) for s in specialists]
    all_sensitivity = [int(s["rubric"]["decisionSensitivity"]) for s in specialists]

    distinct_decisions = sorted(set(s["recommendation"] for s in specialists))
    disagreement_level = 1 if len(distinct_decisions) == 1 else (3 if len(distinct_decisions) == 2 else 5)
    final_decision = consensus_decision
    override_applied = False
    override_reason = None
    human_escalation_reasons: list[str] = []

    strongest_minority = None
    for minority in minority_views:
        if strongest_minority is None:
            strongest_minority = minority
            continue
        candidate_evidence = int(minority["rubric"]["evidenceStrength"])
        current_evidence = int(strongest_minority["rubric"]["evidenceStrength"])
        candidate_rank = decision_rank(minority["recommendation"])
        current_rank = decision_rank(strongest_minority["recommendation"])
        if candidate_evidence > current_evidence or (
            candidate_evidence == current_evidence and candidate_rank > current_rank
        ):
            strongest_minority = minority

    if strongest_minority is not None:
        minority_evidence = int(strongest_minority["rubric"]["evidenceStrength"])
        minority_rank = decision_rank(strongest_minority["recommendation"])
        consensus_rank = decision_rank(consensus_decision)
        if minority_evidence >= 4 and (minority_evidence - consensus_evidence_strength) >= 2 and minority_rank > consensus_rank:
            final_decision = strongest_minority["recommendation"]
            override_applied = True
            override_reason = "Evidence-gated override: minority specialist evidence materially exceeded the consensus evidence base."

    minimum_evidence_completeness = min(all_evidence_completeness)
    minimum_policy_fit = min(all_policy_fit)
    maximum_severity = max(all_severity)
    maximum_sensitivity = max(all_sensitivity)
    overall_confidence = round(sum(all_confidence) / len(all_confidence))

    if minimum_evidence_completeness <= 2 and decision_rank(final_decision) < 2:
        final_decision = "Warn"
        if not override_applied:
            override_applied = True
            override_reason = "Evidence-gated override: evidence completeness was too low to sustain a Pass."

    if disagreement_level >= 4 and overall_confidence <= 2 and decision_rank(final_decision) < 2:
        final_decision = "Warn"
        if not override_applied:
            override_applied = True
            override_reason = "Evidence-gated override: severe specialist disagreement and low confidence prevented a Pass."

    severe_views = [s for s in specialists if int(s["rubric"]["riskSeverity"]) >= 4 and int(s["rubric"]["evidenceStrength"]) >= 4]
    if maximum_severity >= 4 and severe_views:
        final_decision = "Block"
        if not override_applied or decision_rank(final_decision) > decision_rank(consensus_decision):
            override_applied = True
            override_reason = "Severity-and-policy override: a credible high-severity risk met the escalation threshold."

    if minimum_policy_fit <= 2 and decision_rank(final_decision) < 2:
        final_decision = "Warn"
        if not override_applied:
            override_applied = True
            override_reason = "Severity-and-policy override: policy fit was too weak to sustain a Pass."

    if maximum_sensitivity >= 4 and (minimum_evidence_completeness <= 2 or disagreement_level >= 4):
        human_escalation_reasons.append("High-sensitivity case retains unresolved uncertainty.")

    if len(record["permissionEscalationsRequested"]) > len(record["permissionEscalationsApproved"]):
        human_escalation_reasons.append("Permission broadening remains unresolved.")

    sorted_risk_views = sorted(
        specialists,
        key=lambda s: ((int(s["rubric"]["riskSeverity"]) * 10) + int(s["rubric"]["evidenceStrength"])),
        reverse=True,
    )
    top_risks = [
        {
            "role": s["role"],
            "recommendation": s["recommendation"],
            "summary": s["summary"],
            "evidenceRefs": list(s.get("evidenceRefs", [])),
        }
        for s in sorted_risk_views[:3]
    ]

    rule_triggered = (
        "severity-and-policy"
        if override_reason and override_reason.startswith("Severity-and-policy")
        else "evidence-gated"
        if override_reason and override_reason.startswith("Evidence-gated")
        else "consensus"
    )
    decision_path = [
        f"Consensus began at {consensus_decision} with disagreement level {disagreement_level}.",
        f"Overall confidence resolved to {overall_confidence} on the internal 1-5 scale.",
        f"Minimum evidence completeness resolved to {minimum_evidence_completeness} and minimum policy fit resolved to {minimum_policy_fit}.",
    ]
    if override_applied and override_reason:
        decision_path.append(f"Override path: {override_reason}")
    else:
        decision_path.append("No override applied; the adjudicated outcome remained aligned with the consensus decision.")

    uncertainty_drivers: list[str] = []
    if minimum_evidence_completeness <= 2:
        uncertainty_drivers.append("evidence completeness remained low")
    if disagreement_level >= 4:
        uncertainty_drivers.append("specialist disagreement remained high")
    if len(record["permissionEscalationsRequested"]) > len(record["permissionEscalationsApproved"]):
        uncertainty_drivers.append("permission broadening was unresolved")

    residual_risk = {"Pass": "Low", "Warn": "Low-Medium", "Block": "Medium"}[final_decision]

    record["deliberation"]["specialists"] = specialists
    record["deliberation"]["agreement"]["consensusDecision"] = consensus_decision
    record["deliberation"]["agreement"]["disagreementLevel"] = disagreement_level
    record["deliberation"]["agreement"]["summary"] = f"Consensus began at {consensus_decision} with disagreement level {disagreement_level}."
    record["deliberation"]["rubric"]["confidence"] = overall_confidence
    record["deliberation"]["rubric"]["evidenceStrength"] = round(sum(int(s["rubric"]["evidenceStrength"]) for s in specialists) / len(specialists))
    record["deliberation"]["rubric"]["riskSeverity"] = maximum_severity
    record["deliberation"]["rubric"]["evidenceCompleteness"] = minimum_evidence_completeness
    record["deliberation"]["rubric"]["disagreementLevel"] = disagreement_level
    record["deliberation"]["rubric"]["policyFit"] = minimum_policy_fit
    record["deliberation"]["rubric"]["decisionSensitivity"] = maximum_sensitivity
    record["deliberation"]["overrideModel"]["overrideApplied"] = override_applied
    record["deliberation"]["overrideModel"]["overrideReason"] = override_reason
    record["deliberation"]["overrideModel"]["humanEscalationRequired"] = bool(human_escalation_reasons)
    record["deliberation"]["overrideModel"]["humanEscalationReasons"] = human_escalation_reasons
    record["deliberation"]["overrideModel"]["overrideTestSummary"] = override_reason if override_applied and override_reason else "No override was applied because the consensus outcome remained acceptable under the configured rules."
    adjudication = record["deliberation"]["adjudication"]
    adjudication["finalDecision"] = final_decision
    adjudication["finalConfidenceBand"] = confidence_band(overall_confidence)
    adjudication["summary"] = override_reason if override_applied and override_reason else "Orchestrator adjudicated to the consensus outcome without override."
    adjudication["ruleTriggered"] = rule_triggered
    adjudication["humanEscalationConsidered"] = bool(human_escalation_reasons)
    adjudication["residualRiskAfterMitigation"] = residual_risk
    adjudication["decisionPath"] = decision_path
    adjudication["uncertaintyDrivers"] = uncertainty_drivers
    adjudication["supportingEvidence"] = [ref for risk in top_risks for ref in risk.get("evidenceRefs", []) if ref]

    record["deliberation"]["status"] = "completed"
    record["decision"] = final_decision
    record["confidenceBand"] = adjudication["finalConfidenceBand"]
    record["topRisks"] = top_risks
    record["updatedAt"] = utc_now().isoformat().replace("+00:00", "Z")

    _write_json(path, record)
    _write_json(run_dir / "deliberation.json", record["deliberation"])
    return {
        "runId": record["runId"],
        "finalDecision": record["decision"],
        "finalConfidenceBand": record["confidenceBand"],
        "overrideApplied": override_applied,
        "humanEscalationRequired": bool(human_escalation_reasons),
    }
