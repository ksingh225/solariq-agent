
"""Run the Week 5 showcase through the existing Week 3 SolarIQ agent."""

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
WEEK2_APP = REPO_ROOT / "week2-realtime-data" / "app"
WEEK3_APP = REPO_ROOT / "week3-agent" / "app"
WEEK5_APP = Path(__file__).resolve().parent

# Keep the existing Week 3 agent and its tools available.
for entry in (
    str(REPO_ROOT),
    str(WEEK2_APP),
    str(WEEK3_APP),
    str(WEEK5_APP),
):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from agent import SolarAgentDeps, solar_agent
from showcase import build_showcase_inputs


def build_assessment_question(inputs: dict[str, Any]) -> str:
    """Create an evidence-labelled request from the prepared input bundle."""
    return (
        "Assess this SolarIQ demonstration using only the evidence below.\n"
        "IMPORTANT: all plant telemetry is synthetic demonstration data, "
        "not real plant measurements. Identify it as simulated in the "
        "assessment. Do not present it as a real observation.\n"
        "Distinguish simulated telemetry, external weather observations, "
        "and modeled output estimates. Classify every weather-based output "
        "calculated by SolarIQ as evidence_type estimated, and identify its "
        "source as Open-Meteo weather data processed by SolarIQ. Never label "
        "this calculated estimate as user-provided or documented. Preserve "
        "the estimate as distinct from measured plant generation. A gap between simulated measured "
        "power and estimated output does not establish a real plant fault. "
        "Do not invent missing measurements or unsupported root causes. "
        "If measured generation is missing, do not claim or imply that a "
        "measured-versus-expected output gap has been established. State "
        "that performance cannot be confirmed and recommend obtaining "
        "actual generation readings and inverter telemetry. "
        "Preserve the weather source and observation timestamp, including "
        "the timezone, in evidence when available. "
        "Interpret timezone-naive weather timestamps using the supplied "
        "timezone; never assume UTC or relabel local time as UTC. "
        "Follow the time_alignment result in the evidence bundle. If "
        "time_alignment.aligned is false, or its status is not aligned, "
        "do not compare simulated measured power with the weather-based "
        "estimate as if they were synchronized. Explain that the timestamps "
        "are missing, invalid, or outside the configured tolerance, as "
        "indicated by the alignment result. Do not infer a performance gap "
        "from unaligned observations. "
        "High- and critical-risk recommendations must require human "
        "approval. Never directly control equipment.\n\n"
        "Prepared demonstration evidence (JSON):\n"
        f"{inputs}"
    )


async def run_showcase(
    scenario: str,
    capacity_kw: float,
    plant_id: str = "SOLARIQ-DEMO-01",
    fetch_weather: bool = True,
):
    """Build showcase inputs and obtain the existing structured assessment."""
    inputs = await build_showcase_inputs(
        scenario=scenario,
        capacity_kw=capacity_kw,
        plant_id=plant_id,
        fetch_weather=fetch_weather,
    )
    question = build_assessment_question(inputs.model_dump(mode="json"))
    if not fetch_weather:
        weather_status = "not_requested"
    elif inputs.weather is None:
        weather_status = "weather_unavailable"
    else:
        weather_status = "available"

    deps = SolarAgentDeps(weather_status=weather_status)
    return await solar_agent.run(question, deps=deps)
