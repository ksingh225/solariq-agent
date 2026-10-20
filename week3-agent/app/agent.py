
import importlib.util
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import Agent, ModelRetry

from schemas import SolarAssessment
from tools import (
    assess_solar_conditions,
    estimate_solar_output,
    get_live_solar_weather,
    get_solar_knowledge,
)

# Load the repository's local .env file.
load_dotenv()

# Load Week 6 configuration explicitly, avoiding ambiguous module imports.
APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
CONFIG_PATH = (
    REPO_ROOT / "week6-production-readiness" / "app" / "config.py"
)

SPEC = importlib.util.spec_from_file_location(
    "solariq_week6_config", CONFIG_PATH
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load SolarIQ Week 6 configuration.")

CONFIG_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CONFIG_MODULE
SPEC.loader.exec_module(CONFIG_MODULE)

MODEL_NAME = CONFIG_MODULE.get_settings().solariq_model


solar_agent = Agent(
    MODEL_NAME,
    output_type=SolarAssessment,
    system_prompt=(
        "You are SolarIQ, a solar operations decision-support assistant. "
        "Analyze solar plant performance using retrieved solar knowledge "
        "and current weather data when relevant. Distinguish observed "
        "measurements, estimates, documented facts, and hypotheses. "

        "Never invent plant capacity, efficiency, measured generation, "
        "sensor readings, inverter telemetry, or historical trends. "
        "Only use plant capacity and efficiency explicitly supplied by "
        "the user or supported by verified evidence. If plant capacity "
        "is missing, ask the user for it and do not call tools that "
        "estimate plant output using an assumed capacity. Do not assume "
        "a default capacity or infer capacity from the question. "

     "A weather-based output calculation is an estimate, not actual "
"plant generation. Clearly label estimates and explain their "
"limitations. Never present an estimate as a measured result. "
"For every weather-based output estimate, include a limitation "
"stating that the result is modeled from current weather and "
"plant inputs, relies on simplified assumptions, and does not "
"represent measured or actual generation. Mention relevant "
"uncertainties such as changing irradiance, shading, soiling, "
"system losses, or inverter efficiency when applicable. Do not "
"claim these factors were observed unless supported by evidence. "
        "Weather data alone cannot establish underperformance or "
        "confirm a plant fault. When actual plant-generation data is "
        "unavailable, explicitly state that underperformance cannot be "
        "confirmed. Do not infer a fault from cloud cover or "
        "irradiance alone. "

        "Distinguish evidence of an output gap from evidence of its "
        "cause. When the user provides measured and expected output "
        "values, include those values as evidence of the observed gap "
        "in the assessment evidence list, using the correct evidence "
        "types and source. Do not describe expected output as measured "
        "output. Do not assume ideal or clear weather conditions unless "
        "supported by evidence. "

        "Every root-cause hypothesis must include specific supporting "
        "evidence in its evidence field, drawn from evidence provided "
        "by the user or returned by tools. The evidence must actually "
        "support the proposed cause; a measured-versus-expected output "
        "gap alone does not prove shading, equipment malfunction, or "
        "another specific fault. A proposed check or a statement that "
        "more data is needed is not evidence that a fault exists. "
      "If no relevant supporting evidence exists for a specific cause, "
"set root_cause_hypotheses to an empty list and explain which "
"additional measurements are needed. Never invent evidence "
"to satisfy this requirement. "

"When user-provided or tool-provided measured generation is below "
"expected generation, explicitly distinguish the observed output "
"gap from its unknown cause. State that the gap alone does not "
"establish why output is lower. Include at least one actionable, "
"non-invasive diagnostic recommendation, such as reviewing "
"time-aligned generation readings, checking available inverter "
"telemetry and alarm logs, and visually inspecting for shading "
"or soiling where safe. Do not claim that any check has already "
"been performed unless evidence confirms it. Keep routine checks "
"low risk and do not direct physical equipment control. "
        "Before interpreting zero generation, check the observation "
        "timestamp and irradiance when available. Zero irradiance at "
        "night is expected, and zero generation at night is normally "
"When asked whether zero nighttime output indicates a fault, "
"explicitly state that zero generation at night alone does not "
"indicate a fault. Recommend checking daytime generation readings "
"before assessing plant performance. "
        "expected. Explain that daytime generation data is needed "
        "to assess plant performance. When asked whether zero nighttime "
        "output indicates a fault, explicitly recommend checking daytime "
        "generation readings in the structured assessment. "

       "When actual generation readings and inverter telemetry are "
"missing, give a cautious assessment without claiming a "
"confirmed cause. For this situation, set root_cause_hypotheses "
"to an empty list unless there is supporting evidence. You MUST "
"include at least one actionable recommendation in the structured "
"recommendations list: obtain actual generation readings AND "
"inverter telemetry. Classify this routine data collection as low "
"risk and set requires_human_approval to false. Do not leave "
"recommendations empty when this data is missing. State that "
"underperformance cannot be confirmed without measured-generation "
"evidence. Do not use phrases such as "        "'the plant is underperforming' unless supported by observed "
        "measured-generation evidence. Do not repeat an unsupported "
        "claim even to explain why it is uncertain. "

        "Use only evidence returned by tools or provided by the user. "
        "Do not describe current weather as historical or recent trends "
        "unless historical data has actually been retrieved. "

        "Classify routine diagnostic data collection, such as obtaining "
        "generation readings and inverter telemetry, as low risk unless "
        "the action itself introduces a meaningful operational or safety "
        "risk. Classify monitoring and non-invasive diagnostic checks "
        "according to their actual risk. Do not label an action high "
        "risk merely because it supports a plant assessment. "
        "Recommendations involving high or critical risk must require "
        "human approval. Never directly control physical equipment. "
        "Do not invent facts to complete a structured assessment."
    ),
)


@solar_agent.tool_plain
def retrieve_solar_knowledge(query: str) -> dict:
    """Retrieve solar domain knowledge relevant to a question."""
    return get_solar_knowledge(query)


@solar_agent.tool_plain
async def fetch_current_weather() -> dict:
    """Fetch current weather for the configured solar location."""
    return await get_live_solar_weather()


@solar_agent.tool_plain
def calculate_expected_output(
    capacity_kw: float,
    irradiance_wm2: float,
    efficiency: float = 0.80,
) -> dict:
    """Estimate output using the deterministic solar estimator.

    Do not call this tool with an assumed plant capacity.
    """
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
    """Assess current conditions using a supplied or verified capacity.

    Do not call this tool with an assumed plant capacity.
    """
    if capacity_kw <= 0:
        return {
            "status": "missing_or_invalid_capacity",
            "message": (
                "A valid plant capacity greater than zero is required. "
                "Do not estimate output or fetch weather for this assessment. "
                "Ask the user to provide the plant capacity."
            ),
            "limitations": [
                "Plant capacity was not supplied or is invalid.",
                "Underperformance cannot be confirmed without measured "
                "generation data.",
            ],
        }

    return await assess_solar_conditions(
        capacity_kw=capacity_kw,
        efficiency=efficiency,
    )
@solar_agent.output_validator
def validate_solar_assessment(
    assessment: SolarAssessment,
) -> SolarAssessment:
    """Reject unsupported claims that underperformance is established."""

    assessment_text = " ".join(
        [
            assessment.summary,
            *assessment.limitations,
            *[
                f"{item.description} {item.source}"
                for item in assessment.evidence
            ],
            *[
                f"{hypothesis.cause} {hypothesis.reasoning}"
                for hypothesis in assessment.root_cause_hypotheses
            ],
            *[
                recommendation.action
                for recommendation in assessment.recommendations
            ],
        ]
    ).lower()

    measured_terms = (
        "actual generation",
        "measured generation",
        "actual output",
        "measured output",
        "plant telemetry",
    )

    has_measured_evidence = any(
        item.evidence_type == "observed"
        and any(
            term in item.description.lower()
            for term in measured_terms
        )
        for item in assessment.evidence
    )

    unsupported_claims = (
        "the plant is underperforming",
        "the plant is currently underperforming",
        "your plant is underperforming",
        "your plant is currently underperforming",
        "underperformance is occurring",
        "underperformance is confirmed",
        "indicates underperformance",
        "indicating underperformance",
        "plant performance is below",
        "producing less than expected",
        "below expected generation",
        "confirmed solar fault",
    )

    # Avoid common explicit negations triggering a phrase-based false positive.
    cautious_phrases = (
        "underperformance cannot be confirmed",
        "underperformance can't be confirmed",
        "cannot confirm underperformance",
        "unable to confirm underperformance",
        "not confirmed",
        "no evidence of",
        "is not underperforming",
        "isn't underperforming",
    )

    claim_text = assessment_text
    for phrase in cautious_phrases:
        claim_text = claim_text.replace(phrase, "")

    matched_claims = [
        claim
        for claim in unsupported_claims
        if claim in claim_text
    ]

    if not has_measured_evidence and matched_claims:
        raise ModelRetry(
            "Unsupported-claim validator triggered: "
            f"{matched_claims}. No observed measured-generation evidence "
            "was found. State that underperformance cannot be confirmed "
            "without measured generation data, and do not present an "
            "unverified fault as established."
        )

    unsupported_hypotheses = [
        hypothesis.cause
        for hypothesis in assessment.root_cause_hypotheses
        if not hypothesis.evidence
    ]

    if unsupported_hypotheses:
        raise ModelRetry(
            "Each root-cause hypothesis must include supporting evidence, "
            "or be omitted when evidence is insufficient. "
            f"Unsupported hypotheses: {unsupported_hypotheses}"
        )

    return assessment
