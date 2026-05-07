from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
PLUGIN_ROOT = ROOT
CALIBRATION_DB = PLUGIN_ROOT / "calibration" / "premortemx-calibration-python.sqlite"


def run_script(name: str, *args: str) -> tuple[int, str]:
    command = [sys.executable, str(SCRIPTS / name), *args]
    proc = subprocess.run(command, capture_output=True, text=True)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return proc.returncode, output


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    tests_run = 0
    index_path = PLUGIN_ROOT / "registry" / "runs" / "index.jsonl"
    quality_log_path = PLUGIN_ROOT / "registry" / "quality-review-log.json"
    views_root = PLUGIN_ROOT / "registry" / "views"
    index_backup = index_path.read_text(encoding="utf-8") if index_path.exists() else None
    quality_backup = quality_log_path.read_text(encoding="utf-8") if quality_log_path.exists() else None
    views_backup = views_root.exists()

    code, output = run_script("New-PreMortemXRun.py", "--ProjectSlug", "py-sample-api", "--Decision", "Warn")
    assert_true(code == 0, f"Python run initialization should succeed.\n{output}")
    created = json.loads(output)
    run_path = Path(created["RunPath"])
    record_path = Path(created["RecordPath"])
    arch_run_path: Path | None = None
    arch_record_path: Path | None = None

    try:
        assert_true(run_path.exists(), "Python-created run directory should exist.")
        summary_short = (run_path / "summary-short.md").read_text(encoding="utf-8")
        summary_standard = (run_path / "summary-standard.md").read_text(encoding="utf-8")
        summary_exec = (run_path / "summary-exec.md").read_text(encoding="utf-8")
        risk_register = (run_path / "risk-register.md").read_text(encoding="utf-8")
        evidence_index = (run_path / "evidence-index.md").read_text(encoding="utf-8")
        analysis = json.loads((run_path / "analysis.json").read_text(encoding="utf-8"))
        deliberation = json.loads((run_path / "deliberation.json").read_text(encoding="utf-8"))
        assert_true("## Assessment Scope" in summary_short, "Python short summary should include assessment scope.")
        assert_true("## Assessment Scope And Decision Window" in summary_standard, "Python standard summary should include scope and decision window.")
        assert_true("## Decision Owner And Required Action" in summary_standard, "Python standard summary should include decision owner.")
        assert_true("## Decision Required" in summary_exec, "Python exec summary should include decision required.")
        assert_true("## Proceed Conditions" in summary_exec, "Python exec summary should include proceed conditions.")
        assert_true("Likelihood:" in risk_register, "Python risk register should scaffold likelihood.")
        assert_true("Risk owner:" in risk_register, "Python risk register should scaffold risk ownership.")
        assert_true("supports finding IDs" in evidence_index, "Python evidence index should scaffold traceability fields.")
        assert_true("decisionContext" in analysis, "Python analysis scaffold should include decision context.")
        assert_true(len(analysis["findings"]) >= 1, "Python analysis scaffold should include finding placeholders.")
        assert_true(deliberation["overrideModel"]["overrideTestSummary"] == "Pending override evaluation.", "Python deliberation scaffold should include override test summary.")
        tests_run += 1

        code, output = run_script("New-PreMortemXRun.py", "--ProjectSlug", "py-sample-arch", "--Mode", "architecture-validation", "--Decision", "Warn")
        assert_true(code == 0, f"Python architecture run initialization should succeed.\n{output}")
        arch_created = json.loads(output)
        arch_run_path = Path(arch_created["RunPath"])
        arch_record_path = Path(arch_created["RecordPath"])
        arch_record = json.loads(arch_record_path.read_text(encoding="utf-8"))
        arch_summary = (arch_run_path / "summary-standard.md").read_text(encoding="utf-8")
        assert_true(arch_record["mode"] == "architecture-validation", "Python architecture mode should be recorded.")
        assert_true(arch_record["taskType"] == "architecture-review", "Python architecture task type should be recorded.")
        assert_true(arch_record["taskCategory"] == "risk-analysis", "Python architecture task category should default to risk-analysis.")
        assert_true("PreMortemX Architecture Assessment" in arch_summary, "Python architecture summary title should be used.")
        tests_run += 1

        code, output = run_script("Test-PreMortemXRunRecord.py", "--RunRecordPath", str(record_path))
        assert_true(code == 0, f"Python run-record validation should succeed.\n{output}")
        tests_run += 1

        code, output = run_script("Test-PreMortemXRunRecord.py", "--RunRecordPath", str(arch_record_path))
        assert_true(code == 0, f"Python architecture run-record validation should succeed.\n{output}")
        tests_run += 1

        specialist_input = run_path / "specialists-test.json"
        specialist_input.write_text(
            json.dumps(
                {
                    "specialists": [
                        {
                            "role": "Domain Risk Specialist",
                            "recommendation": "Warn",
                            "summary": "The delivery shape is fragile.",
                            "evidenceRefs": ["design/spec.md"],
                            "rubric": {
                                "confidence": 2,
                                "evidenceStrength": 2,
                                "riskSeverity": 3,
                                "evidenceCompleteness": 2,
                                "disagreementLevel": 4,
                                "policyFit": 3,
                                "decisionSensitivity": 3,
                            },
                        },
                        {
                            "role": "Operational/Release Risk Specialist",
                            "recommendation": "Pass",
                            "summary": "Operational controls look manageable.",
                            "evidenceRefs": ["ops/checklist.md"],
                            "rubric": {
                                "confidence": 2,
                                "evidenceStrength": 2,
                                "riskSeverity": 2,
                                "evidenceCompleteness": 2,
                                "disagreementLevel": 4,
                                "policyFit": 3,
                                "decisionSensitivity": 4,
                            },
                        },
                        {
                            "role": "Security/Privacy Risk Specialist",
                            "recommendation": "Block",
                            "summary": "Sensitive path lacks enough evidence controls.",
                            "evidenceRefs": ["security/review.md"],
                            "rubric": {
                                "confidence": 4,
                                "evidenceStrength": 5,
                                "riskSeverity": 5,
                                "evidenceCompleteness": 4,
                                "disagreementLevel": 4,
                                "policyFit": 2,
                                "decisionSensitivity": 5,
                            },
                        },
                    ]
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        code, output = run_script(
            "Invoke-PreMortemXDeliberation.py",
            "--RunRecordPath",
            str(record_path),
            "--SpecialistInputPath",
            str(specialist_input),
        )
        assert_true(code == 0, f"Python deliberation should succeed.\n{output}")
        payload = json.loads(output)
        record = json.loads(record_path.read_text(encoding="utf-8"))
        assert_true(payload["finalDecision"] == "Block", "Python deliberation should escalate to Block.")
        assert_true(record["deliberation"]["status"] == "completed", "Python deliberation status should be completed.")
        assert_true(record["deliberation"]["overrideModel"]["overrideApplied"] is True, "Python override model should record an override.")
        assert_true(record["deliberation"]["overrideModel"]["humanEscalationRequired"] is True, "Python override model should require human escalation.")
        assert_true(record["deliberation"]["adjudication"]["ruleTriggered"] == "severity-and-policy", "Python deliberation should record rule trigger.")
        assert_true(len(record["deliberation"]["adjudication"]["decisionPath"]) >= 1, "Python deliberation should record decision path.")
        assert_true(record["deliberation"]["adjudication"]["humanEscalationConsidered"] is not None, "Python deliberation should record whether human escalation was considered.")
        tests_run += 1

        code, output = run_script("Update-PreMortemXRegistry.py", "--RunRecordPath", str(record_path))
        assert_true(code == 0, f"Python registry update should succeed.\n{output}")
        assert_true(index_path.exists(), "Python registry index should exist.")
        index_content = index_path.read_text(encoding="utf-8")
        assert_true(created["RunId"] in index_content, "Python registry index should contain the run ID.")
        tests_run += 1

        code, output = run_script("Update-PreMortemXRegistry.py", "--RunRecordPath", str(arch_record_path))
        assert_true(code == 0, f"Python architecture registry update should succeed.\n{output}")
        index_content = index_path.read_text(encoding="utf-8")
        assert_true("risk-analysis" in index_content, "Python registry index should contain task category.")
        tests_run += 1

        code, output = run_script("Get-PreMortemXRegistrySummary.py")
        assert_true(code == 0, f"Python registry summary should succeed.\n{output}")
        summary = json.loads(output)
        assert_true(summary["totalRuns"] >= 1, "Python registry summary should report runs.")
        assert_true(summary["byDecision"]["Block"] >= 1, "Python registry summary should count Block decisions.")
        assert_true(summary["pendingQualityFollowup"] >= 1, "Python registry summary should report pending quality follow-up before reviews.")
        tests_run += 1

        code, output = run_script("Build-PreMortemXRegistryViews.py")
        assert_true(code == 0, f"Python registry view build should succeed.\n{output}")
        assert_true((views_root / "dashboard.md").exists(), "Python dashboard should exist.")
        assert_true((views_root / "latest-by-project.json").exists(), "Python latest-by-project view should exist.")
        assert_true((views_root / "attention-queue.json").exists(), "Python attention-queue view should exist.")
        tests_run += 1

        code, output = run_script(
            "Update-PreMortemXQualityReview.py",
            "--RunRecordPath",
            str(record_path),
            "--ReviewOutcome",
            "accurate",
            "--Reviewer",
            "python-evaluator",
            "--OutcomeNotes",
            "Validated-after-python-review.",
        )
        assert_true(code == 0, f"Python quality review update should succeed.\n{output}")
        review = json.loads(output)
        assert_true(review["reviewer"] == "python-evaluator", "Python review should record reviewer.")
        tests_run += 1

        code, output = run_script("Get-PreMortemXGuardrailRecommendations.py", "--ProjectSlug", "py-sample-api")
        assert_true(code == 0, f"Python guardrail recommendations should succeed.\n{output}")
        guardrails = json.loads(output)
        assert_true(guardrails["reviewedRuns"] >= 1, "Python guardrail recommendations should include reviewed runs.")
        tests_run += 1

        code, output = run_script("Get-PreMortemXTrendSummary.py")
        assert_true(code == 0, f"Python trend summary should succeed.\n{output}")
        trend = json.loads(output)
        assert_true(trend["totalReviewed"] >= 1, "Python trend summary should report reviewed items.")
        assert_true(trend["byOutcome"]["accurate"] >= 1, "Python trend summary should count accurate reviews.")
        tests_run += 1

        code, output = run_script("Initialize-PreMortemXCalibrationStore.py", "--DatabasePath", str(CALIBRATION_DB))
        assert_true(code == 0, f"Python calibration init should succeed.\n{output}")
        assert_true(CALIBRATION_DB.exists(), "Python calibration DB should exist.")
        tests_run += 1

        code, output = run_script(
            "Import-PreMortemXReviewedRunToCalibration.py",
            "--RunRecordPath",
            str(record_path),
            "--PromotionState",
            "trusted",
            "--DatasetVersion",
            "v4-seed",
            "--DatabasePath",
            str(CALIBRATION_DB),
        )
        assert_true(code == 0, f"Python reviewed-run import should succeed.\n{output}")
        imported = json.loads(output)
        assert_true(imported["promotionState"] == "trusted", "Python import should set trusted promotion.")
        tests_run += 1

        code, output = run_script("Get-PreMortemXCalibrationSummary.py", "--DatabasePath", str(CALIBRATION_DB))
        assert_true(code == 0, f"Python calibration summary should succeed.\n{output}")
        calibration_summary = json.loads(output)
        assert_true(calibration_summary["totalCases"] >= 1, "Python calibration summary should report cases.")
        assert_true(calibration_summary["byPromotionState"]["trusted"] >= 1, "Python calibration summary should count trusted cases.")
        tests_run += 1

        code, output = run_script(
            "Set-PreMortemXCalibrationPromotionState.py",
            "--CaseId",
            created["RunId"],
            "--PromotionState",
            "provisional",
            "--ChangedBy",
            "python-codex",
            "--Reason",
            "python-state-change",
            "--DatabasePath",
            str(CALIBRATION_DB),
        )
        assert_true(code == 0, f"Python promotion state change should succeed.\n{output}")
        promotion = json.loads(output)
        assert_true(promotion["toState"] == "provisional", "Python promotion should set provisional state.")
        tests_run += 1

        code, output = run_script(
            "Request-PreMortemXCalibrationChange.py",
            "--ChangeTier",
            "TierB",
            "--ChangeType",
            "confidence-band-tuning",
            "--ProposedValue",
            '{"confidence":4}',
            "--Reason",
            "python-regression-tuning",
            "--RequestedBy",
            "python-codex",
            "--DatabasePath",
            str(CALIBRATION_DB),
        )
        assert_true(code == 0, f"Python calibration change request should succeed.\n{output}")
        change_request = json.loads(output)
        tests_run += 1

        code, output = run_script(
            "Approve-PreMortemXCalibrationChange.py",
            "--ChangeRequestId",
            change_request["changeRequestId"],
            "--ApprovalScope",
            "session",
            "--ApprovalDecision",
            "approved",
            "--ApprovedBy",
            "python-codex",
            "--ApprovalNote",
            "python-bounded-approval",
            "--DatabasePath",
            str(CALIBRATION_DB),
        )
        assert_true(code == 0, f"Python calibration approval should succeed.\n{output}")
        approval = json.loads(output)
        assert_true(approval["status"] == "approved", "Python approval should succeed.")
        tests_run += 1

        code, output = run_script("Get-PreMortemXAdvisoryDelegationPlan.py")
        assert_true(code == 0, f"Python advisory plan should succeed.\n{output}")
        advisory = json.loads(output)
        assert_true(advisory["authorityMode"] == "local-only", "Python advisory plan should keep local-only authority.")
        assert_true(len(advisory["optionallyDelegated"]) >= 1, "Python advisory plan should populate optional delegation.")
        tests_run += 1

        code, output = run_script("Get-PreMortemXRegistrySummary.py")
        assert_true(code == 0, f"Python quality-aware registry summary should succeed.\n{output}")
        quality_summary = json.loads(output)
        assert_true(quality_summary["totalReviewed"] >= 1, "Python registry summary should include reviewed counts.")
        assert_true(quality_summary["byReviewOutcome"]["accurate"] >= 1, "Python registry summary should include review outcomes.")
        assert_true(quality_summary["pendingQualityFollowup"] >= 0, "Python registry summary should include pending quality follow-up count.")
        tests_run += 1

        code, output = run_script("Build-PreMortemXRegistryViews.py")
        assert_true(code == 0, f"Python quality-aware registry view build should succeed.\n{output}")
        dashboard = (views_root / "dashboard.md").read_text(encoding="utf-8")
        assert_true("Reviewed runs:" in dashboard, "Python dashboard should include reviewed run counts.")
        assert_true("Pending quality follow-up:" in dashboard, "Python dashboard should include pending quality follow-up.")
        tests_run += 1

        invalid_record = json.loads(record_path.read_text(encoding="utf-8"))
        invalid_record["decision"] = "Maybe"
        record_path.write_text(json.dumps(invalid_record, indent=2), encoding="utf-8")
        code, output = run_script("Test-PreMortemXRunRecord.py", "--RunRecordPath", str(record_path))
        assert_true(code != 0, "Python invalid decision should fail validation.")
        tests_run += 1
    finally:
        if run_path.exists():
            shutil.rmtree(run_path)
        if arch_run_path and arch_run_path.exists():
            shutil.rmtree(arch_run_path)
        if index_backup is None:
            if index_path.exists():
                index_path.unlink()
        else:
            index_path.write_text(index_backup, encoding="utf-8")
        if quality_backup is None:
            if quality_log_path.exists():
                quality_log_path.unlink()
        else:
            quality_log_path.write_text(quality_backup, encoding="utf-8")
        if not views_backup and views_root.exists():
            shutil.rmtree(views_root)
        if CALIBRATION_DB.exists():
            CALIBRATION_DB.unlink()

    print(f"PreMortemX Python runtime tests passed: {tests_run}")


if __name__ == "__main__":
    main()
