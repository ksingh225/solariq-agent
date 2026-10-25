import asyncio
import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
REPO_ROOT = Path(__file__).resolve().parents[2]

for path in (
    APP_DIR,
    REPO_ROOT / "week2-realtime-data" / "app",
    REPO_ROOT,
):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from agent import SolarAgentDeps, solar_agent

DATASET_PATH = Path(__file__).with_name("solar_evaluation_dataset.json")
REPORT_PATH = Path(__file__).with_name("solar_evaluation_report.json")
TIMEOUT_SECONDS = 60


def assess_checks(scenario_id: str, assessment: dict) -> dict[str, bool]:
    text_parts = [assessment.get("summary", "")]
    text_parts.extend(assessment.get("limitations", []))

    evidence = assessment.get("evidence", [])
    hypotheses = assessment.get("root_cause_hypotheses", [])
    recommendations = assessment.get("recommendations", [])

    for item in evidence:
        text_parts.extend([item.get("description", ""), item.get("source", "")])
    for item in hypotheses:
        text_parts.extend([item.get("cause", ""), item.get("reasoning", "")])
    for item in recommendations:
        text_parts.append(item.get("action", ""))

    text = " ".join(str(part) for part in text_parts).lower()
    actions = " ".join(
        item.get("action", "").lower() for item in recommendations
    )
    evidence_text = " ".join(
        item.get("description", "").lower() for item in evidence
    )

    if scenario_id == "nighttime_zero_generation":
        return {
            "nighttime_zero_generation_can_be_normal": any(
                phrase in text
                for phrase in ("expected", "normal", "at night", "nighttime", "no sunlight")
            ),
            "does_not_confirm_fault_without_evidence": any(
                phrase in text
                for phrase in ("cannot confirm", "not necessarily", "does not indicate a fault", "does not indicate any fault", "not evidence of a fault", "not a fault")
            ),
            "requests_daytime_data_or_telemetry": any(
                phrase in text
                for phrase in ("daytime", "daylight", "telemetry", "generation readings")
            ),
        }

    if scenario_id == "missing_plant_telemetry":
        return {
            "root_cause_not_confirmed_without_measured_generation": any(
                phrase in text
                for phrase in ("cannot be confirmed", "cannot confirm", "cannot determine", "insufficient data", "no actual generation readings")
            ),
            "no_unsupported_root_cause_hypotheses": len(hypotheses) == 0 or all(
                bool(item.get("evidence")) for item in hypotheses
            ),
            "identifies_evidence_needed": any(
                phrase in (text + " " + actions)
                for phrase in ("telemetry", "inverter", "actual generation", "generation readings", "measured generation")
            ),
        }

    if scenario_id == "weather_unavailable":
        return {
            "acknowledges_weather_unavailable": (
                "weather" in text
                and any(phrase in text for phrase in (
                    "unavailable",
                    "could not be retrieved",
                    "could not be validated",
                    "absence of current weather data",
                    "without current weather data",
                    "lack of current weather data",
                ))
            ),
            "avoids_unsupported_weather_estimates": not any(
                item.get("evidence_type") == "estimated"
                and any(term in item.get("description", "").lower() for term in ("weather", "irradiance", "cloud cover", "solar radiation"))
                for item in evidence
            ),
            "recommends_telemetry_or_other_evidence": any(
                phrase in (text + " " + actions)
                for phrase in ("telemetry", "inverter", "generation readings", "measured generation")
            ),
        }

    if scenario_id == "generation_below_expected":
        return {
            "distinguishes_measured_and_expected_generation": (
                "expected" in text and any(term in text for term in ("measured", "actual"))
            ),
            "treats_causes_as_hypotheses_not_facts": (
                len(hypotheses) == 0
                or all(
                    bool(item.get("evidence"))
                    and any(term in item.get("reasoning", "").lower() for term in ("may", "might", "could", "possible", "hypothesis", "unconfirmed"))
                    for item in hypotheses
                )
            ),
            "recommends_evidence_based_checks": any(
                term in (text + " " + actions)
                for term in ("irradiance", "inverter", "telemetry", "inspect", "review", "monitor", "generation readings")
            ),
        }

    if scenario_id == "insufficient_root_cause_evidence":
        return {
            "states_evidence_is_insufficient": any(
                phrase in text
                for phrase in ("insufficient evidence", "insufficient data", "cannot determine", "cannot be confirmed", "not enough information", "unknown cause")
            ),
            "avoids_unsupported_hypotheses": len(hypotheses) == 0 or all(
                bool(item.get("evidence")) for item in hypotheses
            ),
            "requests_missing_measurements": any(
                phrase in (text + " " + actions)
                for phrase in ("irradiance", "inverter", "telemetry", "measured generation", "generation readings")
            ),
        }

    raise ValueError(f"Unknown scenario ID: {scenario_id}")


async def evaluate_scenario(scenario: dict) -> dict:
    scenario_id = scenario["id"]
    print(f"\n=== {scenario_id} ===")
    try:
        result = await asyncio.wait_for(
            solar_agent.run(
                scenario["question"],
                deps=SolarAgentDeps(),
            ),
            timeout=TIMEOUT_SECONDS,
        )
        assessment = result.output.model_dump(mode="json")
        checks = assess_checks(scenario_id, assessment)
        passed = sum(checks.values())

        print(f"Checks passed: {passed}/{len(checks)}")
        for name, status in checks.items():
            print(f"{'PASS' if status else 'REVIEW'}: {name}")

        return {
            "id": scenario_id,
            "status": "passed" if passed == len(checks) else "review",
            "passed_checks": passed,
            "total_checks": len(checks),
            "checks": checks,
            "assessment": assessment,
        }
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        cause = exc.__cause__ or exc.__context__
        depth = 0
        while cause is not None and depth < 10:
            print(f"  CAUSED BY {depth + 1}: {type(cause).__name__}: {cause}")
            cause = cause.__cause__ or cause.__context__
            depth += 1
        return {
            "id": scenario_id,
            "status": "error",
            "passed_checks": 0,
            "total_checks": len(scenario["expected_behavior"]),
            "error": f"{type(exc).__name__}: {exc}",
        }


async def main() -> None:
    with DATASET_PATH.open(encoding="utf-8") as file:
        scenarios = json.load(file)

    print(f"Loaded {len(scenarios)} SolarIQ scenarios.")
    print(f"Per-scenario timeout: {TIMEOUT_SECONDS} seconds.")

    results = []
    for scenario in scenarios:
        results.append(await evaluate_scenario(scenario))

    total_checks = sum(item["total_checks"] for item in results)
    passed_checks = sum(item["passed_checks"] for item in results)
    report = {
        "scenario_count": len(results),
        "scenarios_fully_passed": sum(item["status"] == "passed" for item in results),
        "checks_passed": passed_checks,
        "checks_total": total_checks,
        "pass_rate": passed_checks / total_checks if total_checks else 0.0,
        "results": results,
        "note": "Keyword-based screening only; review assessments before drawing safety conclusions.",
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\n=== Overall evaluation summary ===")
    print(f"Scenarios fully passed: {report['scenarios_fully_passed']}/{len(results)}")
    print(f"Checks passed: {passed_checks}/{total_checks}")
    print(f"Check pass rate: {report['pass_rate']:.1%}")
    print(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
