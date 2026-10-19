
import sys
from pathlib import Path

import pytest
from pydantic_ai.models.test import TestModel

ROOT = Path(__file__).resolve().parents[2]

# Keep the repository root first so app.rag resolves to the Week 1 RAG package.
sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(ROOT / "week2-realtime-data" / "app"))
sys.path.insert(2, str(ROOT / "week3-agent" / "app"))

from agent import solar_agent


@pytest.mark.asyncio
async def test_agent_returns_structured_assessment():
    test_model = TestModel(call_tools=[])

    with solar_agent.override(model=test_model):
        result = await solar_agent.run(
            "Assess a hypothetical 5 kW solar system."
        )

    assert result.output.summary
    assert isinstance(result.output.evidence, list)
    assert isinstance(result.output.recommendations, list)


@pytest.mark.asyncio
async def test_agent_can_invoke_registered_tool():
    test_model = TestModel(call_tools=["retrieve_solar_knowledge"])

    with solar_agent.override(model=test_model):
        result = await solar_agent.run(
            "Use solar knowledge to explain low generation."
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
            "Assess current conditions for a hypothetical 5 kW solar system."
        )

    assert result.output.summary
    assert isinstance(result.output.recommendations, list)


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
    from agent import validate_solar_assessment
    from schemas import SolarAssessment

    assessment = SolarAssessment(
        summary="The plant is underperforming.",
        evidence=[],
    )

    with pytest.raises(
        ModelRetry,
        match="Unsupported-claim validator triggered",
    ):
        validate_solar_assessment(assessment)


def test_validator_accepts_cautious_underperformance_statement():
    from agent import validate_solar_assessment
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

    result = validate_solar_assessment(assessment)

    assert result.summary == assessment.summary


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
    from agent import validate_solar_assessment
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
        validate_solar_assessment(assessment)


def test_agent_does_not_assume_missing_plant_capacity():
    instructions = solar_agent._system_prompts
    prompt_text = " ".join(instructions).lower()

    assert "never invent plant capacity" in prompt_text
    assert "if plant capacity is missing" in prompt_text
    assert "do not call tools" in prompt_text
    assert "do not assume a default capacity" in prompt_text

def test_validator_accepts_missing_telemetry_without_confirming_underperformance():
    from agent import validate_solar_assessment
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

    result = validate_solar_assessment(assessment)

    assert result.summary == assessment.summary
    assert result.root_cause_hypotheses == []
    assert len(result.recommendations) == 2

