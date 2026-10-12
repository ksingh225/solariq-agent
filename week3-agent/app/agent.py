
import os

from dotenv import load_dotenv
from pydantic_ai import Agent

from schemas import SolarAssessment
from tools import (
    assess_solar_conditions,
    estimate_solar_output,
    get_live_solar_weather,
    get_solar_knowledge,
)

# Load configuration from the repository's local .env file.
load_dotenv()

MODEL_NAME = os.getenv("SOLARIQ_MODEL", "test")

solar_agent = Agent(
    MODEL_NAME,
    output_type=SolarAssessment,
    system_prompt=(
        "You are SolarIQ, a solar operations decision-support assistant. "
        "Use available tools and evidence to assess potential solar "
        "performance issues. Distinguish observations, estimates, and "
        "hypotheses. Never invent plant telemetry or claim a root cause "
        "is confirmed without sufficient evidence. Explain limitations. "
        "Provide cautious recommendations. Never directly control "
        "physical equipment, and require human approval for high-risk "
        "or critical actions. "
        "Before diagnosing underperformance, check the observation "
        "timestamp and irradiance. Zero irradiance at night is expected "
        "and is not evidence of a plant fault. If the observation is at "
        "night, explain that daytime generation data is needed to assess "
        "performance. Do not infer a fault from weather data alone. "
        "When actual plant-generation data is unavailable, explicitly "
        "state that underperformance cannot be confirmed. "
        "Use only evidence returned by tools or provided by the user. "
        "Do not describe current weather as historical or recent trends "
        "unless historical data has actually been retrieved."
    ),
)


@solar_agent.tool_plain
def retrieve_solar_knowledge(query: str) -> dict:
    """Retrieve solar domain knowledge relevant to a question."""
    return get_solar_knowledge(query)


@solar_agent.tool_plain
async def fetch_current_weather() -> dict:
    """Fetch current solar-site weather."""
    return await get_live_solar_weather()


@solar_agent.tool_plain
def calculate_expected_output(
    capacity_kw: float,
    irradiance_wm2: float,
    efficiency: float = 0.80,
) -> dict:
    """Estimate solar output using deterministic calculations."""
    return estimate_solar_output(
        capacity_kw=capacity_kw,
        irradiance_wm2=irradiance_wm2,
        efficiency=efficiency,
    )


@solar_agent.tool_plain
async def assess_current_solar_conditions(
    capacity_kw: float,
    efficiency: float = 0.80,
) -> dict:
    """Combine current weather with a deterministic solar output estimate."""
    return await assess_solar_conditions(
        capacity_kw=capacity_kw,
        efficiency=efficiency,
    )
