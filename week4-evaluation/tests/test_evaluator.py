
import json
import sys
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

import evaluator
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


def test_load_evaluation_cases_rejects_non_object_entry(tmp_path, monkeypatch):
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(["not an object"]), encoding="utf-8")
    monkeypatch.setattr(evaluator, "DATASET_PATH", path)

    with pytest.raises(ValueError, match="must be a JSON object"):
        evaluator.load_evaluation_cases()


def test_load_evaluation_cases_rejects_duplicate_ids(tmp_path, monkeypatch):
    case = {
        "id": "E01",
        "scenario": "nighttime_zero_generation",
        "input": "Question",
        "expected_behaviors": ["check_a"],
    }
    path = tmp_path / "cases.json"
    path.write_text(json.dumps([case, case]), encoding="utf-8")
    monkeypatch.setattr(evaluator, "DATASET_PATH", path)

    with pytest.raises(ValueError, match="Duplicate evaluation case ID"):
        evaluator.load_evaluation_cases()


def test_load_evaluation_cases_rejects_invalid_expected_behaviors(
    tmp_path, monkeypatch
):
    case = {
        "id": "E01",
        "scenario": "nighttime_zero_generation",
        "input": "Question",
        "expected_behaviors": ["check_a", ""],
    }
    path = tmp_path / "cases.json"
    path.write_text(json.dumps([case]), encoding="utf-8")
    monkeypatch.setattr(evaluator, "DATASET_PATH", path)

    with pytest.raises(ValueError, match="expected_behaviors"):
        evaluator.load_evaluation_cases()


def test_load_evaluation_cases_rejects_empty_input(tmp_path, monkeypatch):
    case = {
        "id": "E01",
        "scenario": "nighttime_zero_generation",
        "input": "   ",
        "expected_behaviors": ["check_a"],
    }
    path = tmp_path / "cases.json"
    path.write_text(json.dumps([case]), encoding="utf-8")
    monkeypatch.setattr(evaluator, "DATASET_PATH", path)

    with pytest.raises(ValueError, match="input"):
        evaluator.load_evaluation_cases()
