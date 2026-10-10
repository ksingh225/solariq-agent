
"""Async client for fetching real-time weather and solar data from Open-Meteo."""

import logging
import time

import httpx

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_solar_weather(
    latitude: float = 17.3850,
    longitude: float = 78.4867,
) -> dict:
    """Fetch current weather and solar irradiance data for a location."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",
            "cloud_cover",
            "shortwave_radiation",
        ],
        "timezone": "Asia/Kolkata",
    }

    start_time = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            data = response.json()

        current = data.get("current")
        if not isinstance(current, dict):
            raise ValueError("Open-Meteo response has no valid 'current' data")

        required_fields = (
            "temperature_2m",
            "cloud_cover",
            "shortwave_radiation",
        )
        missing = [field for field in required_fields if field not in current]
        if missing:
            raise ValueError(f"Missing current weather fields: {missing}")

        result = {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
            "observed_at": current.get("time"),
            "temperature_c": current["temperature_2m"],
            "cloud_cover_percent": current["cloud_cover"],
            "shortwave_radiation_wm2": current["shortwave_radiation"],
            "source": "Open-Meteo",
        }

        logger.info(
            "Open-Meteo request completed in %.3f seconds",
            time.perf_counter() - start_time,
        )
        return result

    except (httpx.HTTPError, ValueError):
        logger.exception("Failed to fetch or validate Open-Meteo data")
        raise
