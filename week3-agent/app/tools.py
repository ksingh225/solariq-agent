
import httpx
from pathlib import Path
import sys
from typing import Any


# Make the repository root available for the Week 1 RAG package.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def get_solar_knowledge(query: str, top_k: int = 3) -> dict[str, Any]:
    """Retrieve solar domain knowledge through the Week 1 RAG service."""
    from app.rag.service import RAGService

    service = RAGService()
    result = service.retrieve(query=query, top_k=top_k)

    return {
        "status": "success",
        "query": result["query"],
        "evidence": result["results"],
    }


async def get_live_solar_weather() -> dict[str, Any]:
    """Fetch current weather using the existing Week 2 client."""
    from weather_client import fetch_solar_weather

    return await fetch_solar_weather()


def estimate_solar_output(
    capacity_kw: float,
    irradiance_wm2: float,
    efficiency: float = 0.80,
) -> dict[str, Any]:
    """Use the existing deterministic Week 2 generation estimate."""
    if capacity_kw <= 0:
        raise ValueError("capacity_kw must be greater than zero")

    from solar_analytics import estimate_solar_generation

    return estimate_solar_generation(
        capacity_kw=capacity_kw,
        irradiance_wm2=irradiance_wm2,
        efficiency=efficiency,
    )


async def assess_solar_conditions(
    capacity_kw: float,
    efficiency: float = 0.80,
) -> dict[str, Any]:
    """Combine current weather with a deterministic solar output estimate."""
    if capacity_kw <= 0:
        raise ValueError("capacity_kw must be greater than zero")

    try:
        weather = await get_live_solar_weather()
    except (TimeoutError, ValueError, httpx.HTTPError):
        return {
            "status": "weather_unavailable",
            "message": (
                "Current weather data is unavailable; "
                "no solar output estimate was calculated."
            ),
            "weather": None,
            "estimate": None,
            "limitations": [
                "Weather data could not be retrieved or validated.",
                "No solar output estimate was calculated.",
                "Actual plant generation must be measured independently.",
            ],
        }

    irradiance_wm2 = weather["shortwave_radiation_wm2"]
    estimate = estimate_solar_output(
        capacity_kw=capacity_kw,
        irradiance_wm2=irradiance_wm2,
        efficiency=efficiency,
    )

    return {
        "status": "success",
        "weather": weather,
        "estimate": estimate,
        "limitations": [
            "Estimated instantaneous output, not measured plant generation.",
            "Shortwave radiation is used as an irradiance proxy.",
            "This is a simplified engineering estimate, not a certified forecast.",
        ],
    }
