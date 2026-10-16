
import os

from dotenv import load_dotenv
from pydantic_ai import Agent, ModelRetry

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

        "Weather data alone cannot establish underperformance or "
        "confirm a plant fault. When actual plant-generation data is "
        "unavailable, explicitly state that underperformance cannot be "
        "confirmed. Do not infer a fault from cloud cover or "
        "irradiance alone. If telemetry is missing, do not present "
        "possible causes as established findings. Label them as "
        "unconfirmed hypotheses or omit them when evidence is "
        "insufficient. Identify the measurements needed for diagnosis. "

        "Before interpreting zero generation, check the observation "
        "timestamp and irradiance when available. Zero irradiance at "
        "night is expected, and zero generation at night is normally "
        "expected. Explain that daytime generation data is needed "
        "to assess plant performance. When asked whether zero nighttime "
        "output indicates a fault, explicitly recommend checking daytime "
        "generation readings in the structured assessment. "

        "When actual generation readings and inverter telemetry are "
        "missing, give a cautious assessment without claiming a "
        "confirmed cause. For this situation, set root_cause_hypotheses "
        "to an empty list unless there is supporting evidence. Recommend "
        "obtaining actual generation readings and inverter telemetry. "
        "State that underperformance cannot be confirmed without "
        "measured-generation evidence. Do not use phrases such as "
        "'the plant is underperforming' unless supported by observed "
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

    return assessment
