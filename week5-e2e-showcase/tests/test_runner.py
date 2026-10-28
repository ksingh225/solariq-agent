import asyncio
import importlib.util
from pathlib import Path

from pydantic_ai.models.test import TestModel


APP_DIR = Path(__file__).resolve().parents[1] / "app"
SPEC = importlib.util.spec_from_file_location(
    "solariq_week5_runner", APP_DIR / "runner.py"
)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_assessment_question_labels_simulated_telemetry():
    question = runner.build_assessment_question(
        {
            "scenario": "potential_output_gap",
            "simulated_telemetry": {
                "source": "simulated",
                "is_simulated": True,
                "measured_power_kw": 25,
            },
            "expected_output_estimate": {
                "estimated_power_kw": 56,
                "model_type": "simplified_engineering_estimate",
            },
        }
    )

    assert "synthetic demonstration data" in question
    assert "not real plant measurements" in question
    assert "does not establish a real plant fault" in question
    assert "measured_power_kw" in question


def test_assessment_question_requires_correct_estimate_provenance():
    question = runner.build_assessment_question(
        {
            "scenario": "potential_output_gap",
            "weather": {
                "source": "Open-Meteo",
                "shortwave_radiation_wm2": 0,
            },
            "expected_output_estimate": {
                "estimated_power_kw": 0,
                "model_type": "simplified_engineering_estimate",
            },
        }
    )

    assert "evidence_type estimated" in question
    assert "Open-Meteo weather data processed by SolarIQ" in question
    assert "Never label this calculated estimate as user-provided or documented" in question

def test_assessment_question_handles_missing_telemetry():
    question = runner.build_assessment_question(
        {
            "scenario": "missing",
            "simulated_telemetry": {
                "source": "simulated",
                "is_simulated": True,
                "measured_power_kw": None,
            },
        }
    )

    assert "measured generation is missing" in question
    assert "inverter telemetry" in question


def test_runner_returns_structured_agent_output(monkeypatch):
    async def fake_build_showcase_inputs(**kwargs):
        class FakeInputs:
            def model_dump(self, mode="python"):
                return {
                    "scenario": kwargs["scenario"],
                    "capacity_kw": kwargs["capacity_kw"],
                    "simulated_telemetry": {
                        "source": "simulated",
                        "is_simulated": True,
                        "measured_power_kw": 60,
                    },
                }

        return FakeInputs()

    monkeypatch.setattr(
        runner,
        "build_showcase_inputs",
        fake_build_showcase_inputs,
    )

    test_model = TestModel(
        call_tools=[],
        custom_output_args={
            "summary": "Performance cannot be confirmed because current weather is unavailable and no weather-based output estimate was calculated.",
            "evidence": [],
            "root_cause_hypotheses": [],
            "recommendations": [{
                "action": "Obtain actual generation readings and inverter telemetry.",
                "risk_level": "low",
                "requires_human_approval": False,
            }],
            "limitations": [
                "Plant telemetry is simulated demonstration data, not real plant data.",
                "Current weather is unavailable; no weather-based output estimate was calculated.",
            ],
        },
    )
    with runner.solar_agent.override(model=test_model):
        result = asyncio.run(
            runner.run_showcase(
                scenario="normal",
                capacity_kw=100,
                fetch_weather=False,
            )
        )

    assert result.output.summary
    assert isinstance(result.output.evidence, list)
    assert isinstance(result.output.recommendations, list)


def test_missing_telemetry_instructions_prevent_unsupported_gap_claims():
    question = runner.build_assessment_question(
        {
            "scenario": "missing",
            "simulated_telemetry": {
                "source": "simulated",
                "is_simulated": True,
                "measured_power_kw": None,
            },
            "weather": {
                "source": "Open-Meteo",
                "observed_at": "2026-10-19T10:00",
            },
            "expected_output_estimate": {
                "estimated_power_kw": 41.6,
                "model_type": "simplified_engineering_estimate",
            },
        }
    )

    assert (
        "do not claim or imply that a measured-versus-expected output gap "
        "has been established"
    ) in question
    assert "Preserve the weather source and observation timestamp" in question
    assert "actual generation readings and inverter telemetry" in question
def test_runner_instructions_reject_unaligned_comparisons():
    question = runner.build_assessment_question(
        {
            "scenario": "potential_output_gap",
            "simulated_telemetry": {
                "source": "simulated",
                "is_simulated": True,
                "observed_at": "2026-10-19T10:00:00+00:00",
                "measured_power_kw": 25,
            },
            "weather": {
                "source": "Open-Meteo",
                "observed_at": "2026-10-19T16:15",
                "timezone": "Asia/Kolkata",
            },
            "time_alignment": {
                "aligned": False,
                "status": "not_aligned",
                "difference_minutes": 45,
                "tolerance_minutes": 15,
                "reason": "Observation timestamps exceed the configured tolerance.",
            },
        }
    )

    assert "Follow the time_alignment result" in question
    assert "do not compare simulated measured power" in question
    assert "Do not infer a performance gap from unaligned observations" in question



def test_runner_marks_offline_weather_as_not_requested(monkeypatch):
    captured = {}

    async def fake_build_showcase_inputs(**kwargs):
        class FakeInputs:
            weather = None

            def model_dump(self, mode="python"):
                return {
                    "scenario": kwargs["scenario"],
                    "capacity_kw": kwargs["capacity_kw"],
                    "simulated_telemetry": {
                        "source": "simulated",
                        "is_simulated": True,
                        "measured_power_kw": 60,
                    },
                    "weather": None,
                }

        return FakeInputs()

    async def fake_agent_run(question, deps):
        captured["weather_status"] = deps.weather_status

        class FakeResult:
            class Output:
                summary = "Offline test assessment."
                evidence = []
                recommendations = []

            output = Output()

        return FakeResult()

    monkeypatch.setattr(runner, "build_showcase_inputs", fake_build_showcase_inputs)
    monkeypatch.setattr(runner.solar_agent, "run", fake_agent_run)

    asyncio.run(
        runner.run_showcase(
            scenario="normal",
            capacity_kw=100,
            fetch_weather=False,
        )
    )

    assert captured["weather_status"] == "not_requested"
