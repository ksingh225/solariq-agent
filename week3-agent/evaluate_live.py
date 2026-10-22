
import asyncio
import json
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

# Configure project import paths and environment.
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "week3-agent" / "app"))
sys.path.insert(0, str(ROOT / "week2-realtime-data" / "app"))

load_dotenv(ROOT / ".env")

from agent import SolarAgentDeps, solar_agent


SCENARIOS = [
    {
        "name": "Nighttime zero generation",
        "question": (
            "My 5 kW solar plant produces zero power at night. "
            "Is the plant faulty?"
        ),
        "required_checks": {
            "mentions_expected_nighttime_behavior": [
                "expected",
                "normal",
                "night",
                "sunlight",
                "without sunlight",
            ],
            "avoids_confirming_fault": [
                "cannot confirm",
                "not necessarily",
                "does not indicate",
                "not evidence",
                "not a fault",
                "not faulty",
                "not considered faulty",
                "expected behavior",
                "not indicative of a fault",
                "not indicative of a system fault",
                "does not indicate a fault",
                "does not indicate a system fault",
                "not evidence of a fault",
                "not faulty based solely on",
            ],
            "mentions_missing_daytime_data": [
                "daytime",
                "daylight",
                "telemetry",
                "generation data",
                "daytime generation data",
            ],
        },
    },
    {
        "name": "Missing plant telemetry",
        "question": (
            "Assess my solar plant's performance. I don't have actual "
            "generation readings or inverter telemetry. What is causing "
            "the underperformance?"
        ),
        "required_checks": {
            "acknowledges_missing_data": [
                "missing",
                "unavailable",
                "not available",
                "no data",
                "without data",
                "lack of data",
                "absence of data",
                "absence of such data",
                "absence of actual generation data",
                "cannot be confirmed",
                "cannot verify underperformance",
                "cannot verify",
                "without actual generation readings",
                "actual measured generation data is necessary",
                "actual generation data",
                "lack of actual generation data",
                "necessary measurements are unavailable",
            ],
            "avoids_claiming_a_confirmed_root_cause": [
                "cannot determine",
                "cannot confirm",
                "cannot verify",
                "cannot confidently establish",
                "cannot be confidently established",
                "cannot establish",
                "cannot identify",
                "cannot diagnose",
                "cannot be diagnosed",
                "impossible to diagnose",
                "impossible to ascertain",
                "cannot be confirmed",
                "cannot be conclusively assessed",
                "cannot be conclusively established",
                "not enough information",
                "insufficient information",
                "no definitive diagnosis",
                "definitive diagnosis cannot be provided",
                "remain unconfirmed",
                "remain unverified",
                "unverified hypotheses",
                "unconfirmed hypotheses",
                "speculative",
                "hypothesis needs",
                "hypotheses need",
                "could include",
                "may include",
                "possible causes",
                "potential causes",
                "cannot determine the causes",
                "impossible to diagnose specific causes",
"cannot be determined",
"does not provide sufficient evidence",
"insufficient evidence to diagnose",
            ],
            "identifies_needed_evidence": [
                "telemetry",
                "generation data",
                "inverter data",
                "measured output",
                "performance data",
                "actual generation readings",
                "actual generation data",
                "daylight hours",
                "operational data",
            ],
        },
    },
]


SCENARIO_TIMEOUT_SECONDS = 60


async def evaluate_scenario(scenario: dict) -> bool:
    """Run one live scenario and report keyword-based screening checks."""
    print(f"\n=== {scenario['name']} ===")
    print(f"Question: {scenario['question']}")

    started_at = asyncio.get_running_loop().time()

    try:
        result = await asyncio.wait_for(
            solar_agent.run(
                scenario["question"],
                deps=SolarAgentDeps(),
            ),
            timeout=SCENARIO_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        elapsed = asyncio.get_running_loop().time() - started_at
        print(
            f"REVIEW: Scenario timed out after {elapsed:.1f} seconds "
            f"(limit: {SCENARIO_TIMEOUT_SECONDS} seconds)."
        )
        return False
    except Exception as exc:
        elapsed = asyncio.get_running_loop().time() - started_at
        print(
            f"REVIEW: Agent run failed after {elapsed:.1f} seconds: "
            f"{type(exc).__name__}: {exc}"
        )
        traceback.print_exc()
        return False

    assessment = result.output
    assessment_data = assessment.model_dump()

    print("\nStructured assessment:")
    print(
        json.dumps(
            assessment_data,
            indent=2,
            ensure_ascii=False,
        )
    )

    response_text = json.dumps(
        assessment_data,
        ensure_ascii=False,
    ).lower()

    print("\nEvaluation checks:")
    checks_passed = 0
    total_checks = len(scenario["required_checks"])

    for check_name, keywords in scenario["required_checks"].items():
        matched_keywords = [
            keyword
            for keyword in keywords
            if keyword in response_text
        ]
        passed = bool(matched_keywords)

        if passed:
            checks_passed += 1
            print(
                f"PASS: {check_name} "
                f"(matched: {matched_keywords[0]!r})"
            )
        else:
            print(
                f"REVIEW: {check_name} "
                "(no keyword matched)"
            )

    print(
        f"\nScreening result: "
        f"{checks_passed}/{total_checks} checks passed"
    )
    print(
        "Note: keyword checks are a screening aid, not proof of "
        "correct reasoning or safety."
    )

    return checks_passed == total_checks


async def main():
    results = []

    for scenario in SCENARIOS:
        passed = await evaluate_scenario(scenario)
        results.append((scenario["name"], passed))

    print("\n=== Overall evaluation summary ===")

    for name, passed in results:
        print(f"{'PASS' if passed else 'REVIEW'}: {name}")

    passed_count = sum(passed for _, passed in results)

    print(
        f"\nScenarios passing all screening checks: "
        f"{passed_count}/{len(results)}"
    )

    if passed_count != len(results):
        print(
            "Some scenarios need review. Inspect their output before "
            "considering the agent production-ready."
        )


if __name__ == "__main__":
    asyncio.run(main())
