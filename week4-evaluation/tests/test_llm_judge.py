import asyncio
import sys
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

from llm_judge import judge_assessment, validate_judge_result


def make_result():
    return {
        "behavior_evaluations": [
            {
                "behavior": "do_not_confirm_a_fault",
                "passed": True,
                "rationale": "The assessment does not assert a fault.",
                "evidence": "A fault cannot be confirmed from the available data.",
            },
            {
                "behavior": "recommend_daytime_check",
                "passed": False,
                "rationale": "No daytime check is recommended.",
                "evidence": "No relevant recommendation was provided.",
            },
        ],
        "overall_score": 0.5,
        "summary": "One behavior passed and one failed.",
        "needs_human_review": False,
    }


def test_valid_judge_result_is_accepted():
    expected = ["do_not_confirm_a_fault", "recommend_daytime_check"]

    result = validate_judge_result(expected, make_result())

    assert result["overall_score"] == 0.5
    assert len(result["behavior_evaluations"]) == 2


def test_missing_behavior_is_rejected():
    expected = ["do_not_confirm_a_fault", "recommend_daytime_check"]
    result = make_result()
    result["behavior_evaluations"].pop()
    result["overall_score"] = 1.0

    with pytest.raises(ValueError, match="behavior mismatch"):
        validate_judge_result(expected, result)


def test_unexpected_behavior_is_rejected():
    expected = ["do_not_confirm_a_fault", "recommend_daytime_check"]
    result = make_result()
    result["behavior_evaluations"][1]["behavior"] = "unexpected_behavior"

    with pytest.raises(ValueError, match="behavior mismatch"):
        validate_judge_result(expected, result)


def test_duplicate_behavior_is_rejected():
    expected = ["do_not_confirm_a_fault", "recommend_daytime_check"]
    result = make_result()
    result["behavior_evaluations"][1]["behavior"] = "do_not_confirm_a_fault"

    with pytest.raises(ValueError, match="duplicate"):
        validate_judge_result(expected, result)


def test_inconsistent_overall_score_is_rejected():
    expected = ["do_not_confirm_a_fault", "recommend_daytime_check"]
    result = make_result()
    result["overall_score"] = 1.0

    with pytest.raises(ValueError, match="does not match"):
        validate_judge_result(expected, result)


def test_judge_requires_explicit_model_configuration(monkeypatch):
    monkeypatch.delenv("SOLARIQ_JUDGE_MODEL", raising=False)

    case = {
        "scenario": "test",
        "input": "Test input",
        "expected_behaviors": ["do_not_confirm_a_fault"],
    }

    with pytest.raises(RuntimeError, match="SOLARIQ_JUDGE_MODEL"):
        asyncio.run(judge_assessment(case, {"summary": "Test"}))
