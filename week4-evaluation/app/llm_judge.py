"""Optional, structured LLM judge for SolarIQ evaluation cases."""

import json
import os
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent

load_dotenv()


class BehaviorEvaluation(BaseModel):
    """Judge decision for one expected behavior."""

    model_config = ConfigDict(extra="forbid")

    behavior: str = Field(min_length=1)
    passed: bool
    rationale: str = Field(min_length=1)
    evidence: str = Field(
        description="A short quotation or precise observation from the assessment."
    )


class JudgeResult(BaseModel):
    """Structured result returned by the LLM judge."""

    model_config = ConfigDict(extra="forbid")

    behavior_evaluations: list[BehaviorEvaluation]
    overall_score: float = Field(ge=0.0, le=1.0)
    summary: str = Field(min_length=1)
    needs_human_review: bool


JUDGE_SYSTEM_PROMPT = """
You are an independent evaluator of a solar-energy decision-support assistant.

Assess only the supplied assessment against the supplied expected behaviors.
Use the assessment's actual content as evidence. Do not assume missing facts.
Distinguish observed measurements from estimates, hypotheses, and assumptions.
Penalize unsupported root-cause claims and unsafe recommendations.
For high-risk or critical-risk actions, require appropriate human approval.
Routine, low-risk data collection should not automatically require approval.

For every expected behavior, return exactly one evaluation:
- passed: true only when the assessment adequately demonstrates the behavior.
- rationale: concise explanation grounded in the assessment.
- evidence: a short quotation or precise observation from the assessment.

The overall score is the fraction of expected behaviors adequately satisfied.
Set needs_human_review to true when evidence is insufficient, the result is
ambiguous, or a safety-critical judgment cannot be confidently established.
Do not treat your judgment as a substitute for deterministic safety checks.
"""


def validate_judge_result(
    expected_behaviors: list[str],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Validate that the judge returned exactly the requested behaviors."""
    parsed = JudgeResult.model_validate(result)
    returned = [item.behavior for item in parsed.behavior_evaluations]

    if len(returned) != len(set(returned)):
        raise ValueError("Judge returned duplicate behavior evaluations.")

    if set(returned) != set(expected_behaviors):
        missing = sorted(set(expected_behaviors) - set(returned))
        unexpected = sorted(set(returned) - set(expected_behaviors))
        raise ValueError(
            f"Judge behavior mismatch. Missing: {missing}; "
            f"unexpected: {unexpected}"
        )

    actual_score = (
        sum(item.passed for item in parsed.behavior_evaluations)
        / len(expected_behaviors)
        if expected_behaviors
        else 0.0
    )

    if abs(parsed.overall_score - actual_score) > 0.001:
        raise ValueError(
            "Judge overall_score does not match its behavior-level results."
        )

    return parsed.model_dump(mode="json")


async def judge_assessment(
    case: dict[str, Any],
    assessment: dict[str, Any],
    model: str | None = None,
) -> dict[str, Any]:
    """Evaluate an assessment using an explicitly configured judge model."""
    judge_model = model or os.getenv("SOLARIQ_JUDGE_MODEL")

    if not judge_model:
        raise RuntimeError(
            "LLM judge is disabled. Set SOLARIQ_JUDGE_MODEL explicitly "
            "before making judge model calls."
        )

    expected_behaviors = case["expected_behaviors"]
    if not expected_behaviors:
        raise ValueError("The evaluation case has no expected behaviors.")

    agent = Agent(
        judge_model,
        output_type=JudgeResult,
        system_prompt=JUDGE_SYSTEM_PROMPT,
    )

    prompt = (
        "Evaluate this SolarIQ assessment.\n\n"
        f"Scenario: {case['scenario']}\n"
        f"User input: {case['input']}\n"
        "Expected behaviors:\n"
        f"{json.dumps(expected_behaviors, indent=2)}\n\n"
        "SolarIQ assessment:\n"
        f"{json.dumps(assessment, indent=2, ensure_ascii=False)}"
    )

    response = await agent.run(prompt)
    return validate_judge_result(
        expected_behaviors,
        response.output.model_dump(mode="json"),
    )
