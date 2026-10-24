
import sys
from pathlib import Path

import pytest
from pydantic_ai.models.test import TestModel

ROOT = Path(__file__).resolve().parents[2]

# Keep the repository root first so app.rag resolves to the Week 1 RAG package.
sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(ROOT / "week2-realtime-data" / "app"))
sys.path.insert(2, str(ROOT / "week3-agent" / "app"))

from agent import SolarAgentDeps, solar_agent


@pytest.mark.asyncio
async def test_agent_returns_structured_assessment():
    test_model = TestModel(call_tools=[])

    with solar_agent.override(model=test_model):
        result = await solar_agent.run(
            "Assess a hypothetical 5 kW solar system.",
            deps=SolarAgentDeps(),
        )

    assert result.output.summary
    assert isinstance(result.output.evidence, list)
    assert isinstance(result.output.recommendations, list)


@pytest.mark.asyncio
async def test_agent_can_invoke_registered_tool():
    test_model = TestModel(call_tools=["retrieve_solar_knowledge"])

    with solar_agent.override(model=test_model):
        result = await solar_agent.run(
            "Use solar knowledge to explain low generation.",
            deps=SolarAgentDeps(),
        )

    assert result.output.summary
    assert result.output.evidence is not None


def test_rag_tool_returns_real_knowledge():
    from tools import get_solar_knowledge

    result = get_solar_knowledge(
        "What factors can reduce solar generation?",
        top_k=3,
    )

    assert result["status"] == "success"
    assert result["query"] == "What factors can reduce solar generation?"
    assert len(result["evidence"]) > 0
    assert "text" in result["evidence"][0]
    assert "source" in result["evidence"][0]


@pytest.mark.asyncio
async def test_agent_can_invoke_combined_solar_assessment(monkeypatch):
    expected = {
        "status": "success",
        "weather": {
            "shortwave_radiation_wm2": 700,
            "temperature_c": 30.0,
            "cloud_cover_percent": 20,
            "source": "Open-Meteo",
        },
        "estimate": {
            "capacity_kw": 5,
            "irradiance_wm2": 700,
            "efficiency": 0.80,
            "estimated_power_kw": 2.8,
            "model_type": "simplified_engineering_estimate",
        },
        "limitations": ["Test estimate only"],
    }

    async def fake_assessment(capacity_kw, efficiency=0.80):
        return expected

    monkeypatch.setattr(
        "agent.assess_solar_conditions",
        fake_assessment,
    )

    test_model = TestModel(
        call_tools=["assess_current_solar_conditions"]
    )

    with solar_agent.override(model=test_model):
        result = await solar_agent.run(
            "Assess current conditions for a hypothetical 5 kW solar system.",
            deps=SolarAgentDeps(),
        )

    assert result.output.summary
    assert isinstance(result.output.recommendations, list)


@pytest.mark.asyncio
async def test_combined_assessment_records_weather_status(monkeypatch):
    from agent import assess_current_solar_conditions

    async def fake_assessment(capacity_kw, efficiency=0.80):
        return {
            "status": "weather_unavailable",
            "weather": None,
            "estimate": None,
            "limitations": ["Weather unavailable"],
        }

    monkeypatch.setattr(
        "agent.assess_solar_conditions",
        fake_assessment,
    )

    deps = SolarAgentDeps()
    ctx = type("TestContext", (), {"deps": deps})()

    result = await assess_current_solar_conditions(
        ctx,
        capacity_kw=5,
    )

    assert result["status"] == "weather_unavailable"
    assert deps.weather_status == "weather_unavailable"


def test_agent_instructions_handle_nighttime_conditions():
    instructions = solar_agent._system_prompts
    prompt_text = " ".join(instructions).lower()

    assert "zero irradiance at night is expected" in prompt_text
    assert (
        "daytime generation data is needed" in prompt_text
        or "daytime generation readings are needed" in prompt_text
    )
    assert "underperformance cannot be confirmed" in prompt_text


def test_validator_rejects_unsupported_underperformance_claim():
    from pydantic_ai import ModelRetry
    from agent import validate_solar_assessment_rules
    from schemas import SolarAssessment

    assessment = SolarAssessment(
        summary="The plant is underperforming.",
        evidence=[],
    )

    with pytest.raises(
        ModelRetry,
        match="Unsupported-claim validator triggered",
    ):
        validate_solar_assessment_rules(assessment)


def test_validator_accepts_cautious_underperformance_statement():
    from agent import validate_solar_assessment_rules
    from schemas import SolarAssessment

    assessment = SolarAssessment(
        summary=(
            "Underperformance cannot be confirmed without actual "
            "generation readings."
        ),
        evidence=[],
        limitations=[
            "Actual generation data is needed to assess performance."
        ],
    )

    result = validate_solar_assessment_rules(assessment)

    assert result.summary == assessment.summary


def test_validator_accepts_alternative_weather_unavailable_wording():
    from agent import validate_solar_assessment_rules
    from schemas import SolarAssessment

    assessment = SolarAssessment(
        summary=(
            "Weather information cannot be obtained, so no weather-based "
            "output estimate was calculated. The cause of the reported "
            "low output cannot be confirmed."
        ),
        evidence=[],
        root_cause_hypotheses=[],
        recommendations=[],
        limitations=[
            "Check actual generation readings and inverter telemetry."
        ],
    )

    result = validate_solar_assessment_rules(
        assessment,
        weather_status="weather_unavailable",
    )

    assert result.summary == assessment.summary


def test_validator_accepts_cautiously_attributed_reported_generation_gap():
    from agent import validate_solar_assessment_rules
    from schemas import SolarAssessment

    assessment = SolarAssessment(
        summary=(
            "The user reports measured daytime generation is below "
            "expected generation, but this has not been independently "
            "verified. The cause is unknown."
        ),
        evidence=[],
        root_cause_hypotheses=[],
        limitations=[
            "Actual generation readings and telemetry are needed "
            "to verify the reported gap."
        ],
    )

    result = validate_solar_assessment_rules(assessment)

    assert result.summary == assessment.summary


def test_validator_still_rejects_unattributed_generation_gap_without_evidence():
    from pydantic_ai import ModelRetry
    from agent import validate_solar_assessment_rules
    from schemas import SolarAssessment

    assessment = SolarAssessment(
        summary="Measured daytime generation is below expected generation.",
        evidence=[],
    )

    with pytest.raises(
        ModelRetry,
        match="Unsupported-claim validator triggered",
    ):
        validate_solar_assessment_rules(assessment)


def test_routine_data_collection_does_not_require_high_risk():
    from schemas import Recommendation

    recommendation = Recommendation(
        action=(
            "Obtain actual generation readings and inverter telemetry "
            "to assess plant performance."
        ),
        risk_level="low",
        requires_human_approval=False,
    )

    assert recommendation.risk_level == "low"
    assert recommendation.requires_human_approval is False


def test_validator_rejects_root_cause_hypothesis_without_evidence():
    from pydantic_ai import ModelRetry
    from agent import validate_solar_assessment_rules
    from schemas import RootCauseHypothesis, SolarAssessment

    assessment = SolarAssessment(
        summary=(
            "The measured output is lower than expected, "
            "but the cause is not confirmed."
        ),
        evidence=[],
        root_cause_hypotheses=[
            RootCauseHypothesis(
                cause="Potential inverter malfunction",
                reasoning=(
                    "The output gap may suggest an equipment issue."
                ),
                evidence=[],
            )
        ],
    )

    with pytest.raises(ModelRetry):
        validate_solar_assessment_rules(assessment)


def test_agent_does_not_assume_missing_plant_capacity():
    instructions = solar_agent._system_prompts
    prompt_text = " ".join(instructions).lower()

    assert "never invent plant capacity" in prompt_text
    assert "if plant capacity is missing" in prompt_text
    assert "do not call tools" in prompt_text
    assert "do not assume a default capacity" in prompt_text


def test_validator_accepts_missing_telemetry_without_confirming_underperformance():
    from agent import validate_solar_assessment_rules
    from schemas import Recommendation, SolarAssessment

    assessment = SolarAssessment(
        summary=(
            "Underperformance cannot be confirmed because actual "
            "generation readings and inverter telemetry are unavailable."
        ),
        evidence=[],
        root_cause_hypotheses=[],
        recommendations=[
            Recommendation(
                action="Obtain actual generation readings.",
                risk_level="low",
                requires_human_approval=False,
            ),
            Recommendation(
                action="Collect inverter telemetry.",
                risk_level="low",
                requires_human_approval=False,
            ),
        ],
        limitations=[
            "The cause cannot be determined without measured-generation data."
        ],
    )

    result = validate_solar_assessment_rules(assessment)

    assert result.summary == assessment.summary
    assert result.root_cause_hypotheses == []
    assert len(result.recommendations) == 2


@pytest.mark.asyncio
async def test_agent_handles_weather_unavailable_without_claiming_output(
    monkeypatch,
):
    unavailable = {
        "status": "weather_unavailable",
        "message": (
            "Current weather data is unavailable; "
            "no solar output estimate was calculated."
        ),
        "weather": None,
        "estimate": None,
        "limitations": [
            "Weather data could not be retrieved or validated.",
            "No solar output estimate was calculated.",
            "Actual plant generation must be measured independently.",
        ],
    }

    async def fake_assessment(capacity_kw, efficiency=0.80):
        return unavailable

    monkeypatch.setattr(
        "agent.assess_solar_conditions",
        fake_assessment,
    )

    test_model = TestModel(
        call_tools=["assess_current_solar_conditions"],
        custom_output_args={
            "summary": (
                "Current weather is unavailable, so no solar output "
                "estimate can be calculated."
            ),
            "evidence": [],
            "root_cause_hypotheses": [],
            "recommendations": [
                {
                    "action": (
                        "Obtain actual generation readings and inverter "
                        "telemetry to assess plant performance."
                    ),
                    "risk_level": "low",
                    "requires_human_approval": False,
                }
            ],
            "limitations": [
                "Weather data is unavailable.",
                "Underperformance cannot be confirmed without measured "
                "generation data.",
            ],
        },
    )

    with solar_agent.override(model=test_model):
        result = await solar_agent.run(
            "Assess current conditions for a hypothetical 5 kW solar system.",
            deps=SolarAgentDeps(),
        )

    assert result.output.summary
    assert result.output.root_cause_hypotheses == []

    assessment_text = " ".join(
        [
            result.output.summary,
            *result.output.limitations,
            *[
                recommendation.action
                for recommendation in result.output.recommendations
            ],
        ]
    ).lower()

    assert "weather" in assessment_text
    assert (
        "unavailable" in assessment_text
        or "no solar output estimate was calculated" in assessment_text
        or "cannot be calculated" in assessment_text
    )


@pytest.mark.asyncio
async def test_standalone_weather_tool_records_unavailable_status(monkeypatch):
    from agent import fetch_current_weather

    async def failing_weather():
        raise TimeoutError("Weather request timed out")

    monkeypatch.setattr("agent.get_live_solar_weather", failing_weather)

    deps = SolarAgentDeps()
    ctx = type("TestContext", (), {"deps": deps})()

    result = await fetch_current_weather(ctx)

    assert result["status"] == "weather_unavailable"
    assert result["weather"] is None
    assert result["estimate"] is None
    assert deps.weather_status == "weather_unavailable"


def test_validator_accepts_user_provided_measured_vs_expected_gap():
    from agent import validate_solar_assessment_rules
    from schemas import Evidence, SolarAssessment

    assessment = SolarAssessment(
        summary=(
            "Measured daytime generation is below expected generation. "
            "This observed gap does not establish its cause."
        ),
        evidence=[
            Evidence(
                description=(
                    "The user reports measured daytime generation "
                    "below expected generation."
                ),
                source="User input",
                evidence_type="observed",
            )
        ],
        root_cause_hypotheses=[],
    )

    result = validate_solar_assessment_rules(assessment)

    assert result.summary == assessment.summary
    assert result.root_cause_hypotheses == []
