
import importlib.util
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx

from dotenv import load_dotenv
from pydantic_ai import Agent, ModelRetry, RunContext

from schemas import SolarAssessment
from tools import (
    assess_solar_conditions,
    estimate_solar_output,
    get_live_solar_weather,
    get_solar_knowledge,
)


@dataclass
class SolarAgentDeps:
    """State isolated to a single SolarIQ run."""

    weather_status: str = "not_requested"


# Load the repository's local .env file.
load_dotenv()

# Load Week 6 configuration explicitly, avoiding ambiguous module imports.
APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
CONFIG_PATH = (
    REPO_ROOT / "week6-production-readiness" / "app" / "config.py"
)

SPEC = importlib.util.spec_from_file_location(
    "solariq_week6_config",
    CONFIG_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load SolarIQ Week 6 configuration.")

CONFIG_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CONFIG_MODULE
SPEC.loader.exec_module(CONFIG_MODULE)

MODEL_NAME = CONFIG_MODULE.get_settings().solariq_model


solar_agent = Agent(
    MODEL_NAME,
    deps_type=SolarAgentDeps,
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
        "confirmed. Do not infer a fault from cloud cover or irradiance "
        "alone. If current weather is unavailable, explicitly report "
        "that limitation and do not invent weather values or calculate "
        "a weather-based output estimate. "

        "Distinguish evidence of an output gap from evidence of its "
        "cause. When the user provides both measured and expected output "
        "values, create two separate evidence items, not one combined "
        "item. The measured value must be a separate observed item whose "
        "description explicitly identifies measured output and its value; "
        "use source 'user-provided'. The expected value must be a separate "
        "documented item whose description explicitly identifies expected "
        "output and its value; use source 'user-provided'. Do not label "
        "expected output as measured output or combine both classifications "
        "in one evidence item. Do not assume ideal or clear weather "
        "conditions unless supported by evidence. "

        "Classify evidence according to what it represents and where it "
        "comes from. A user-reported measurement is observed evidence, "
        "with its source identified as user-provided; this does not mean "
        "it has been independently verified. Treat a user-provided expected "
        "output as a documented reference value for classification purposes, "
        "while retaining source 'user-provided'; this does not imply external "
        "documentation or independent verification. Use estimated only for "
        "modeled or calculated values, such as a weather-based generation "
        "estimate. Do not create a separate estimated evidence item merely "
        "to restate a comparison already reported by the user. Use documented "
        "for facts supported by retrieved manuals, SOPs, or other "
        "documentation when those are the source. Never imply independent "
        "verification unless a tool or source supports it. "

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
        "expected generation, explicitly state in the summary that measured "
        "generation is below expected generation. Clearly distinguish the "
        "measured value from the expected value; do not invent numerical "
        "values when they are not provided. Explain that the observed output "
        "gap is separate from its unknown cause. State that the gap alone does not "
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
        "expected. When asked whether zero nighttime output indicates "
        "a fault, explicitly state that zero generation at night alone "
        "does not indicate a fault. Recommend checking daytime generation "
        "readings before assessing plant performance. Explain that "
        "daytime generation data is needed to assess plant performance. "

        "When actual generation readings and inverter telemetry are "
        "missing, give a cautious assessment without claiming a "
        "confirmed cause. Set root_cause_hypotheses to an empty list "
        "unless there is supporting evidence. Include at least one "
        "actionable recommendation in the structured recommendations "
        "list: obtain actual generation readings and inverter telemetry. "
        "Classify this routine data collection as low risk and set "
        "requires_human_approval to false. Do not leave recommendations "
        "empty when this data is missing. State that underperformance "
        "cannot be confirmed without measured-generation evidence. "
        "Do not use phrases such as 'the plant is underperforming' "
        "unless supported by observed measured-generation evidence. "
        "Do not repeat an unsupported claim even to explain why it is "
        "uncertain. "

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


@solar_agent.tool
async def fetch_current_weather(
    ctx: RunContext[SolarAgentDeps],
) -> dict:
    """Fetch current weather and record its availability for this run."""
    try:
        result = await get_live_solar_weather()
    except (TimeoutError, ValueError, httpx.HTTPError):
        ctx.deps.weather_status = "weather_unavailable"
        return {
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

    ctx.deps.weather_status = "available"
    return result


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


@solar_agent.tool
async def assess_current_solar_conditions(
    ctx: RunContext[SolarAgentDeps],
    capacity_kw: float,
    efficiency: float = 0.80,
) -> dict:
    """Assess current conditions using a supplied or verified capacity.

    Do not call this tool with an assumed plant capacity.
    """
    if capacity_kw <= 0:
        ctx.deps.weather_status = "missing_or_invalid_capacity"
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

    result = await assess_solar_conditions(
        capacity_kw=capacity_kw,
        efficiency=efficiency,
    )

    # Record the status in this run's dependency object only.
    status = result.get("status")
    if status:
        ctx.deps.weather_status = status
    elif result.get("weather") is not None and result.get("estimate") is not None:
        # Preserve compatibility with successful assessment results
        # that do not explicitly return a status field.
        ctx.deps.weather_status = "available"
    else:
        ctx.deps.weather_status = "unknown"

    return result


def validate_solar_assessment_rules(
    assessment: SolarAssessment,
    weather_status: str = "not_requested",
) -> SolarAssessment:
    """Reject unsupported claims and weather-dependent conclusions."""

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

    # When weather retrieval failed, reject weather-derived estimates.
    if weather_status == "weather_unavailable":
        weather_terms = (
            "weather",
            "irradiance",
            "solar radiation",
            "cloud cover",
        )
        weather_estimates = [
            item.description
            for item in assessment.evidence
            if item.evidence_type == "estimated"
            and any(
                term in f"{item.description} {item.source}".lower()
                for term in weather_terms
            )
        ]

        if weather_estimates:
            raise ModelRetry(
                "Weather is unavailable. Do not present a weather-based "
                "estimate as evidence. Explain the unavailable weather "
                "data and request independently measured generation "
                "readings and inverter telemetry."
            )

        # A hypothesis needs independent evidence if weather is unavailable.
        has_observed_generation_evidence = any(
            item.evidence_type == "observed"
            and any(
                term in item.description.lower()
                for term in (
                    "actual generation",
                    "measured generation",
                    "actual output",
                    "measured output",
                    "plant telemetry",
                )
            )
            for item in assessment.evidence
        )

        if (
            assessment.root_cause_hypotheses
            and not has_observed_generation_evidence
        ):
            raise ModelRetry(
                "Current weather is unavailable and no observed measured-"
                "generation evidence supports a root-cause assessment. "
                "Omit root-cause hypotheses and request actual generation "
                "readings and inverter telemetry."
            )

        weather_failure_acknowledged = (
            "weather" in assessment_text
            and any(
                phrase in assessment_text
                for phrase in (
                    "unavailable",
                    "could not be retrieved",
                    "could not be validated",
                    "cannot be obtained",
                    "cannot obtain",
                    "not available",
                    "unable to obtain",
                )
            )
        )
        if not weather_failure_acknowledged:
            raise ModelRetry(
                "The weather tool reported weather_unavailable. Explicitly "
                "state that current weather data is unavailable and that "
                "no weather-based output estimate was calculated."
            )

    measured_terms = (
        "actual generation",
        "measured generation",
        "measured daytime generation",
        "actual daytime generation",
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
        "the plant is underperforming cannot be confirmed",
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

    reported_gap_is_cautiously_attributed = (
        any(
            phrase in assessment_text
            for phrase in (
                "the user reports measured daytime generation",
                "the user reports measured generation",
                "reported by the user",
                "the question reports",
                "the scenario reports",
                "reported measured generation",
            )
        )
        and any(
            phrase in assessment_text
            for phrase in (
                "not been independently verified",
                "not independently verified",
                "cannot be independently verified",
                "has not been verified",
                "the cause is unknown",
                "does not establish its cause",
                "does not establish the cause",
                "does not establish why",
                "cannot confirm underperformance",
                "underperformance cannot be confirmed",
            )
        )
    )

    matched_claims = [
        claim
        for claim in unsupported_claims
        if claim in claim_text
        and not (
            claim == "below expected generation"
            and reported_gap_is_cautiously_attributed
        )
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


@solar_agent.output_validator
def validate_solar_assessment(
    ctx: RunContext[SolarAgentDeps],
    assessment: SolarAssessment,
) -> SolarAssessment:
    """Validate safety rules and preserve explicit input measurements."""
    prompt = ctx.prompt if isinstance(ctx.prompt, str) else ""
    expected_match = re.search(
        r"\bexpected\s+(?:output|generation)\s*(?:is|of|:|=)?\s*(\d+(?:\.\d+)?)",
        prompt,
        re.IGNORECASE,
    )
    measured_match = re.search(
        r"\bmeasured\s+(?:output|generation)\s*(?:is|of|:|=)?\s*(\d+(?:\.\d+)?)",
        prompt,
        re.IGNORECASE,
    )

    if expected_match and measured_match:
        assessment_text = " ".join(
            [
                assessment.summary,
                *assessment.limitations,
                *[item.description for item in assessment.evidence],
                *[item.action for item in assessment.recommendations],
                *[
                    f"{hypothesis.cause} {hypothesis.reasoning}"
                    for hypothesis in assessment.root_cause_hypotheses
                ],
            ]
        )
        missing_values = [
            value
            for value in (expected_match.group(1), measured_match.group(1))
            if value not in assessment_text
        ]
        if missing_values:
            raise ModelRetry(
                "Preserve both numeric values explicitly supplied in the "
                "question. Include the expected and measured output values "
                "in the assessment before drawing conclusions. Missing "
                f"value(s): {', '.join(missing_values)}."
            )

    return validate_solar_assessment_rules(
        assessment,
        weather_status=ctx.deps.weather_status,
    )
