import json
from pathlib import Path
from typing import Any

DATASET_PATH = (
    Path(__file__).resolve().parents[1] / "evaluation_cases.json"
)


def load_evaluation_cases() -> list[dict[str, Any]]:
    """Load and validate the evaluation dataset."""
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    if not isinstance(cases, list):
        raise ValueError("Evaluation dataset must be a JSON array.")

    for case in cases:
        for field in ("id", "scenario", "input", "expected_behaviors"):
            if field not in case:
                raise ValueError(f"Evaluation case is missing field: {field}")

    return cases


def evaluate_response(
    expected_behaviors: list[str],
    checks: dict[str, bool],
) -> dict[str, Any]:
    """Score explicitly supplied deterministic checks."""
    results = {
        behavior: bool(checks.get(behavior, False))
        for behavior in expected_behaviors
    }

    total = len(results)
    passed = sum(results.values())

    return {
        "passed": passed,
        "total": total,
        "score": passed / total if total else 0.0,
        "checks": results,
    }


def main() -> None:
    cases = load_evaluation_cases()
    print(f"Loaded {len(cases)} evaluation cases.")

    for case in cases:
        print(
            f"{case['id']} | {case['scenario']} | "
            f"{len(case['expected_behaviors'])} expected behaviours"
        )

    print(
        "\nDataset loaded successfully. "
        "Response checks will be added in the next step."
    )


if __name__ == "__main__":
    main()
