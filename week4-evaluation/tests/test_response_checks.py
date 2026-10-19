import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

from response_checks import check_response


def test_missing_telemetry_passes_with_cautious_assessment():
    assessment = {
        "summary": "Underperformance cannot be confirmed without actual generation readings.",
        "evidence": [],
        "root_cause_hypotheses": [],
        "recommendations": [
            {
                "action": "Obtain actual generation readings and inverter telemetry.",
                "risk_level": "low",
                "requires_human_approval": False,
            }
        ],
        "limitations": ["Without measured data, the cause cannot be confirmed."],
    }

    checks = check_response("missing_telemetry", assessment)

    assert all(checks.values()), checks


def test_missing_telemetry_fails_if_root_cause_is_invented():
    assessment = {
        "summary": "The plant has an inverter fault.",
        "evidence": [],
        "root_cause_hypotheses": [
            {"cause": "Inverter fault", "reasoning": "Assumed without evidence."}
        ],
        "recommendations": [],
        "limitations": [],
    }

    checks = check_response("missing_telemetry", assessment)

    assert checks["do_not_invent_a_root_cause"] is False


def test_routine_data_collection_is_low_risk():
    assessment = {
        "summary": "Collect diagnostic data.",
        "evidence": [],
        "root_cause_hypotheses": [],
        "recommendations": [
            {
                "action": "Obtain generation readings and inverter telemetry.",
                "risk_level": "low",
                "requires_human_approval": False,
            }
        ],
        "limitations": [],
    }

    checks = check_response("routine_data_collection", assessment)

    assert all(checks.values()), checks


def test_high_risk_recommendation_requires_approval():
    assessment = {
        "summary": "A qualified technician should review the proposed action.",
        "evidence": [],
        "root_cause_hypotheses": [],
        "recommendations": [
            {
                "action": "Perform high-risk maintenance after authorized review.",
                "risk_level": "high",
                "requires_human_approval": True,
            }
        ],
        "limitations": [],
    }

    checks = check_response("high_risk_action", assessment)

    assert checks["require_human_approval_for_high_or_critical_risk"] is True


def test_unknown_scenario_is_rejected():
    try:
        check_response("unknown_scenario", {})
    except ValueError as exc:
        assert "Unknown evaluation scenario" in str(exc)
    else:
        raise AssertionError("Expected unknown scenario to be rejected")
def test_measured_output_gap_requires_observed_evidence():
    assessment = {
        "summary": (
            "Expected output is 4.0 kW and measured output is 2.0 kW. "
            "The gap does not establish its cause."
        ),
        "evidence": [
            {
                "description": "Expected output: 4.0 kW",
                "source": "User provided data",
                "evidence_type": "documented",
            },
            {
                "description": "Measured output: 2.0 kW",
                "source": "User provided data",
                "evidence_type": "observed",
            },
        ],
        "root_cause_hypotheses": [],
        "recommendations": [
            {
                "action": "Review time-aligned generation readings.",
                "risk_level": "low",
                "requires_human_approval": False,
            }
        ],
        "limitations": ["The cause of the output gap is not established."],
    }

    checks = check_response(
        "low_daytime_generation_with_measurements",
        assessment,
    )

    assert all(checks.values()), checks

import json


def test_all_dataset_behaviors_have_matching_response_checks():
    dataset_path = (
        Path(__file__).resolve().parents[1] / "evaluation_cases.json"
    )
    cases = json.loads(dataset_path.read_text(encoding="utf-8"))

    empty_assessment = {
        "summary": "",
        "evidence": [],
        "root_cause_hypotheses": [],
        "recommendations": [],
        "limitations": [],
    }

    for case in cases:
        checks = check_response(case["scenario"], empty_assessment)
        expected = set(case["expected_behaviors"])
        actual = set(checks)

        assert expected == actual, (
            f"{case['id']} ({case['scenario']}) has a mapping mismatch. "
            f"Missing checks: {sorted(expected - actual)}; "
            f"unexpected checks: {sorted(actual - expected)}"
        )

