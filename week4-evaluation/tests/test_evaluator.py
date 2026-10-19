import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.append(str(APP_DIR))
from evaluator import evaluate_response
def test_all_expected_behaviors_pass():
    expected = ["check_a", "check_b"]
    checks = {"check_a": True, "check_b": True}

    result = evaluate_response(expected, checks)

    assert result["passed"] == 2
    assert result["total"] == 2
    assert result["score"] == 1.0


def test_failed_behavior_reduces_score():
    expected = ["check_a", "check_b"]
    checks = {"check_a": True, "check_b": False}

    result = evaluate_response(expected, checks)

    assert result["passed"] == 1
    assert result["total"] == 2
    assert result["score"] == 0.5


def test_missing_check_fails_safely():
    expected = ["check_a"]
    checks = {}

    result = evaluate_response(expected, checks)

    assert result["passed"] == 0
    assert result["total"] == 1
    assert result["score"] == 0.0


def test_empty_expected_behaviors():
    result = evaluate_response([], {})

    assert result["passed"] == 0
    assert result["total"] == 0
    assert result["score"] == 0.0
