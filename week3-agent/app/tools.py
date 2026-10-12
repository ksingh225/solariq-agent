from typing import Any


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
    weather = await get_live_solar_weather()

    irradiance_wm2 = weather["shortwave_radiation_wm2"]
    estimate = estimate_solar_output(
        capacity_kw=capacity_kw,
        irradiance_wm2=irradiance_wm2,
        efficiency=efficiency,
    )

    return {
        "weather": weather,
        "estimate": estimate,
        "limitations": [
            "Estimated instantaneous output, not measured plant generation.",
            "Shortwave radiation is used as an irradiance proxy.",
            "This is a simplified engineering estimate, not a certified forecast.",
        ],
    }
