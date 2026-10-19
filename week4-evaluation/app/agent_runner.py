import asyncio
import sys
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
WEEK3_APP = REPO_ROOT / "week3-agent" / "app"
WEEK2_APP = REPO_ROOT / "week2-realtime-data" / "app"

for path in (WEEK3_APP, WEEK2_APP, REPO_ROOT):
    path_string = str(path)
    if path_string not in sys.path:
        sys.path.insert(0, path_string)

from agent import solar_agent


async def run_assessment(question: str) -> dict[str, Any]:
    """Run the existing Week 3 agent and return its structured assessment."""
    result = await solar_agent.run(question)
    return result.output.model_dump(mode="json")


def main() -> None:
    question = input("Enter a SolarIQ evaluation question: ").strip()

    if not question:
        print("Please enter a question.")
        return

    assessment = asyncio.run(run_assessment(question))

    import json
    print(json.dumps(assessment, indent=2))


if __name__ == "__main__":
    main()
