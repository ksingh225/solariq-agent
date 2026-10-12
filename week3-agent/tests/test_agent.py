import sys
from pathlib import Path

import pytest
from pydantic_ai.models.test import TestModel

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "week2-realtime-data" / "app"))
sys.path.insert(0, str(ROOT / "week3-agent" / "app"))

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
    from tools import assess_solar_conditions

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

    test_model = TestModel(call_tools=["assess_current_solar_conditions"])

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
    assert "daytime generation data is needed" in prompt_text
    assert "underperformance cannot be confirmed" in prompt_text
