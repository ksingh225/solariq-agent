import asyncio
import json
import sys
import traceback
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]

sys.path.insert(0, str(APP_DIR))

from agent_runner import run_assessment
from evaluator import evaluate_response, load_evaluation_cases
from response_checks import check_response

SCENARIO_TIMEOUT_SECONDS = 60


async def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    case_id = case["id"]
    scenario = case["scenario"]

    try:
        assessment = await asyncio.wait_for(
            run_assessment(case["input"]),
            timeout=SCENARIO_TIMEOUT_SECONDS,
        )

        checks = check_response(scenario, assessment)
        result = evaluate_response(case["expected_behaviors"], checks)

        return {
            "id": case_id,
            "scenario": scenario,
            "status": "passed" if result["passed"] == result["total"] else "failed",
            "passed_checks": result["passed"],
            "total_checks": result["total"],
            "score": result["score"],
            "checks": result["checks"],
            "assessment": assessment,
        }

    except Exception as exc:
        traceback.print_exc()
        return {
            "id": case_id,
            "scenario": scenario,
            "status": "error",
            "passed_checks": 0,
            "total_checks": len(case["expected_behaviors"]),
            "score": 0.0,
            "error": f"{type(exc).__name__}: {exc}",
        }


async def main() -> None:
    cases = load_evaluation_cases()
    results = []

    print(f"Running {len(cases)} SolarIQ evaluation scenarios.")
    print(f"Per-scenario timeout: {SCENARIO_TIMEOUT_SECONDS} seconds.")

    for case in cases:
        print(f"\n=== {case['id']}: {case['scenario']} ===")
        result = await evaluate_case(case)
        results.append(result)

        print(
            f"Status: {result['status']} | "
            f"Checks: {result['passed_checks']}/{result['total_checks']}"
        )

        for name, passed in result.get("checks", {}).items():
            print(f"{'PASS' if passed else 'FAIL'}: {name}")

        if "error" in result:
            print(f"ERROR: {result['error']}")

    total_checks = sum(item["total_checks"] for item in results)
    passed_checks = sum(item["passed_checks"] for item in results)
    fully_passed = sum(item["status"] == "passed" for item in results)

    report = {
        "scenario_count": len(results),
        "scenarios_fully_passed": fully_passed,
        "checks_passed": passed_checks,
        "checks_total": total_checks,
        "pass_rate": passed_checks / total_checks if total_checks else 0.0,
        "results": results,
    }

    output_path = REPO_ROOT / "week4-evaluation" / "evaluation_report.json"
    output_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\n=== Overall evaluation summary ===")
    print(f"Scenarios fully passed: {fully_passed}/{len(results)}")
    print(f"Checks passed: {passed_checks}/{total_checks}")
    print(f"Check pass rate: {report['pass_rate']:.1%}")
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
