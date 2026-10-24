import json
from pathlib import Path


DATASET_PATH = Path(__file__).with_name("solar_evaluation_dataset.json")
REQUIRED_FIELDS = {"id", "question", "expected_behavior"}


def load_dataset() -> list[dict]:
    """Load and validate the offline SolarIQ evaluation dataset."""
    with DATASET_PATH.open(encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("The evaluation dataset must be a JSON list.")

    seen_ids = set()

    for index, scenario in enumerate(data):
        if not isinstance(scenario, dict):
            raise ValueError(f"Scenario at index {index} must be an object.")

        missing = REQUIRED_FIELDS - scenario.keys()
        if missing:
            raise ValueError(
                f"Scenario at index {index} is missing fields: "
                f"{sorted(missing)}"
            )

        scenario_id = scenario["id"]
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            raise ValueError(
                f"Scenario at index {index} has an invalid ID."
            )

        if scenario_id in seen_ids:
            raise ValueError(f"Duplicate scenario ID: {scenario_id}")

        if not isinstance(scenario["question"], str) or not scenario["question"].strip():
            raise ValueError(f"Scenario {scenario_id} has an invalid question.")

        behaviors = scenario["expected_behavior"]
        if (
            not isinstance(behaviors, list)
            or not behaviors
            or not all(
                isinstance(item, str) and item.strip()
                for item in behaviors
            )
        ):
            raise ValueError(
                f"Scenario {scenario_id} must have non-empty "
                "expected_behavior criteria."
            )

        seen_ids.add(scenario_id)

    return data


def main() -> None:
    scenarios = load_dataset()
    total_criteria = sum(
        len(scenario["expected_behavior"]) for scenario in scenarios
    )

    print("SolarIQ Offline Evaluation Dataset")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Scenarios: {len(scenarios)}")
    print(f"Expected behavior criteria: {total_criteria}")

    for scenario in scenarios:
        print(
            f"- {scenario['id']}: "
            f"{len(scenario['expected_behavior'])} criteria"
        )

    print("Dataset validation: PASS")


if __name__ == "__main__":
    main()
