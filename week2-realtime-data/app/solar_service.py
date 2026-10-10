"""Combine live weather data with solar generation estimates."""

import importlib.util
from pathlib import Path

from weather_client import fetch_solar_weather


_ANALYTICS_PATH = Path(__file__).with_name("solar_analytics.py")
_spec = importlib.util.spec_from_file_location(
    "solariq_week2_solar_analytics", _ANALYTICS_PATH
)
_analytics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_analytics)

estimate_solar_generation = _analytics.estimate_solar_generation


async def get_solar_assessment(
    capacity_kw: float = 5.0,
    latitude: float = 17.3850,
    longitude: float = 78.4867,
    efficiency: float = 0.80,
) -> dict:
    """Fetch weather and estimate instantaneous solar power."""
    weather = await fetch_solar_weather(latitude, longitude)

    estimate = estimate_solar_generation(
        capacity_kw=capacity_kw,
        irradiance_wm2=weather["shortwave_radiation_wm2"],
        efficiency=efficiency,
    )

    return {
        "location": {
            "latitude": weather["latitude"],
            "longitude": weather["longitude"],
            "timezone": weather["timezone"],
        },
        "observed_at": weather["observed_at"],
        "weather": weather,
        "solar_estimate": estimate,
        "assessment_type": "simplified_estimate_not_certified_forecast",
    }