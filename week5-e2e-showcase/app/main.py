"""Command-line entry point for the SolarIQ Week 5 showcase."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from runner import run_showcase


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the SolarIQ Week 5 end-to-end showcase."
    )
    parser.add_argument(
        "--scenario",
        choices=("normal", "potential_output_gap", "missing"),
        default="potential_output_gap",
        help="Simulated telemetry scenario.",
    )
    parser.add_argument(
        "--capacity-kw",
        type=float,
        required=True,
        help="Explicit configured capacity of the demo plant, in kW.",
    )
    parser.add_argument(
        "--plant-id",
        default="SOLARIQ-DEMO-01",
        help="Identifier for the simulated demo plant.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip live weather retrieval and its output estimate.",
    )
    return parser.parse_args()


async def async_main():
    args = parse_args()

    if args.capacity_kw <= 0:
        raise SystemExit("--capacity-kw must be greater than zero")

    result = await run_showcase(
        scenario=args.scenario,
        capacity_kw=args.capacity_kw,
        plant_id=args.plant_id,
        fetch_weather=not args.offline,
    )

    print("\n--- SolarIQ Week 5 Assessment ---")
    print(result.output.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(async_main())
