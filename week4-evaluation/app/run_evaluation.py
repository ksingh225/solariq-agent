import argparse
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


async def evaluate_case(
    case: dict[str, Any],
    enable_llm_judge: bool = False,
) -> dict[str, Any]:
    case_id = case["id"]
    scenario = case["scenario"]

    try:
        assessment = await asyncio.wait_for(
            run_assessment(case["input"]),
            timeout=SCENARIO_TIMEOUT_SECONDS,
        )

        checks = check_response(scenario, assessment)
        result = evaluate_response(case["expected_behaviors"], checks)

        case_result = {
            "id": case_id,
            "scenario": scenario,
            "status": "passed" if result["passed"] == result["total"] else "failed",
            "passed_checks": result["passed"],
            "total_checks": result["total"],
            "score": result["score"],
            "checks": result["checks"],
            "assessment": assessment,
        }

        if enable_llm_judge:
            from llm_judge import judge_assessment

            try:
                judge_result = await asyncio.wait_for(
                    judge_assessment(case, assessment),
                    timeout=SCENARIO_TIMEOUT_SECONDS,
                )
                case_result["llm_judge"] = judge_result
            except Exception as exc:
                traceback.print_exc()
                case_result["llm_judge"] = {
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                    "needs_human_review": True,
                }

        return case_result

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


async def main(
    enable_llm_judge: bool = False,
    enable_evidently: bool = False,
) -> None:
    cases = load_evaluation_cases()
    results = []

    print(f"Running {len(cases)} SolarIQ evaluation scenarios.")
    print(f"Per-scenario timeout: {SCENARIO_TIMEOUT_SECONDS} seconds.")
    print(f"LLM judge enabled: {enable_llm_judge}")
    print(f"Evidently reporting enabled: {enable_evidently}")

    for case in cases:
        print(f"\n=== {case['id']}: {case['scenario']} ===")
        result = await evaluate_case(case, enable_llm_judge=enable_llm_judge)
        results.append(result)

        print(
            f"Status: {result['status']} | "
            f"Checks: {result['passed_checks']}/{result['total_checks']}"
        )

        for name, passed in result.get("checks", {}).items():
            print(f"{'PASS' if passed else 'FAIL'}: {name}")

        if "llm_judge" in result:
            judge = result["llm_judge"]
            if judge.get("status") == "error":
                print(f"LLM judge error: {judge['error']}")
            else:
                print(
                    f"LLM judge score: {judge['overall_score']:.1%} | "
                    f"Human review: {judge['needs_human_review']}"
                )

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

    if enable_evidently:
        from evidently_report import generate_evidently_report

        evidently_dir = REPO_ROOT / "week4-evaluation" / "evidently_reports"
        paths = generate_evidently_report(report, evidently_dir)
        print("\n=== Evidently reports ===")
        print(f"HTML report: {paths['html']}")
        print(f"JSON report: {paths['json']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate SolarIQ scenarios with optional judge and reporting."
    )
    parser.add_argument(
        "--llm-judge",
        action="store_true",
        help="Enable optional LLM-as-a-Judge evaluation; may incur API costs.",
    )
    parser.add_argument(
        "--evidently",
        action="store_true",
        help="Generate separate Evidently HTML and JSON reports.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        main(
            enable_llm_judge=args.llm_judge,
            enable_evidently=args.evidently,
        )
    )
