import asyncio
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
WEEK2_APP = REPO_ROOT / "week2-realtime-data" / "app"

from agent import solar_agent

for path in (str(APP_DIR), str(WEEK2_APP), str(REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)
async def main():
    question = input(
        "Ask SolarIQ a question about solar performance: "
    ).strip()

    if not question:
        print("Please enter a question.")
        return

    result = await solar_agent.run(question)

    print("\n--- SolarIQ Assessment ---")
    print(result.output.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())