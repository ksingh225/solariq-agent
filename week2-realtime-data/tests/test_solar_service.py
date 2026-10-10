import asyncio
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


APP_DIR = Path(__file__).resolve().parents[1] / "app"

# Load the service and its sibling modules from the Week 2 folder.
import sys
sys.path.insert(0, str(APP_DIR))

try:
    import solar_service
finally:
    sys.path.pop(0)


@pytest.mark.asyncio
async def test_combines_weather_and_solar_estimate():
    fake_weather = {
        "latitude": 17.385,
        "longitude": 78.4867,
        "timezone": "Asia/Kolkata",
        "observed_at": "2026-10-10T12:00",
        "temperature_c": 32.0,
        "cloud_cover_percent": 20,
        "shortwave_radiation_wm2": 500.0,
        "source": "Open-Meteo",
    }

    with patch.object(
        solar_service,
        "fetch_solar_weather",
        new_callable=AsyncMock,
        return_value=fake_weather,
    ):
        result = await solar_service.get_solar_assessment(
            capacity_kw=5.0
        )

    assert result["weather"]["source"] == "Open-Meteo"
    assert result["observed_at"] == "2026-10-10T12:00"
    assert result["solar_estimate"]["estimated_power_kw"] == 2.0
    assert (
        result["assessment_type"]
        == "simplified_estimate_not_certified_forecast"
    )


@pytest.mark.asyncio
async def test_propagates_weather_api_error():
    with patch.object(
        solar_service,
        "fetch_solar_weather",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Weather API unavailable"),
    ):
        with pytest.raises(RuntimeError, match="Weather API unavailable"):
            await solar_service.get_solar_assessment()