import asyncio
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

import llm_judge
import run_evaluation


def test_judge_error_does_not_override_deterministic_result(monkeypatch):
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
        "limitations": [
            "Without measured data, the cause cannot be confirmed."
        ],
    }

    case = {
        "id": "E02",
        "scenario": "missing_telemetry",
        "input": (
            "Assess my plant. I have no actual generation readings or "
            "inverter telemetry. What is causing underperformance?"
        ),
        "expected_behaviors": [
            "state_underperformance_cannot_be_confirmed",
            "do_not_invent_a_root_cause",
            "recommend_obtaining_generation_readings_and_telemetry",
        ],
    }

    async def fake_run_assessment(_question):
        return assessment

    async def fake_judge_assessment(_case, _assessment):
        raise RuntimeError("Simulated judge failure")

    monkeypatch.setattr(
        run_evaluation, "run_assessment", fake_run_assessment
    )
    monkeypatch.setattr(
        llm_judge, "judge_assessment", fake_judge_assessment
    )

    result = asyncio.run(
        run_evaluation.evaluate_case(case, enable_llm_judge=True)
    )

    assert result["status"] == "passed"
    assert result["passed_checks"] == result["total_checks"]
    assert result["llm_judge"]["status"] == "error"
    assert result["llm_judge"]["needs_human_review"] is True
    assert "Simulated judge failure" in result["llm_judge"]["error"]
