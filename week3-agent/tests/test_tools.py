import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "week2-realtime-data" / "app"))
sys.path.insert(0, str(ROOT / "week3-agent" / "app"))

import tools


@pytest.mark.asyncio
async def test_weather_tool_returns_mocked_weather(monkeypatch):
    expected = {
        "latitude": 17.385,
        "longitude": 78.4867,
        "timezone": "Asia/Kolkata",
        "observed_at": "2026-10-12T10:00",
        "temperature_c": 30.0,
        "cloud_cover_percent": 20,
        "shortwave_radiation_wm2": 700,
        "source": "Open-Meteo",
    }

    async def fake_fetch_solar_weather():
        return expected

    monkeypatch.setattr(
        "weather_client.fetch_solar_weather",
        fake_fetch_solar_weather,
    )

    result = await tools.get_live_solar_weather()

    assert result == expected


def test_analytics_tool_returns_deterministic_estimate():
    result = tools.estimate_solar_output(
        capacity_kw=5,
        irradiance_wm2=700,
        efficiency=0.80,
    )

    assert result["estimated_power_kw"] == 2.8
    assert result["model_type"] == "simplified_engineering_estimate"
@pytest.mark.asyncio
async def test_assess_solar_conditions_combines_weather_and_estimate(
    monkeypatch,
):
    weather = {
        "latitude": 17.385,
        "longitude": 78.4867,
        "timezone": "Asia/Kolkata",
        "observed_at": "2026-10-12T10:00",
        "temperature_c": 30.0,
        "cloud_cover_percent": 20,
        "shortwave_radiation_wm2": 700,
        "source": "Open-Meteo",
    }

    async def fake_weather():
        return weather

    monkeypatch.setattr(tools, "get_live_solar_weather", fake_weather)

    result = await tools.assess_solar_conditions(capacity_kw=5)

    assert result["weather"] == weather
    assert result["estimate"]["estimated_power_kw"] == 2.8
    assert result["estimate"]["model_type"] == "simplified_engineering_estimate"
    assert len(result["limitations"]) >= 1
@pytest.mark.asyncio
async def test_assess_solar_conditions_rejects_zero_capacity():
    with pytest.raises(
        ValueError,
        match="capacity_kw must be greater than zero",
    ):
        await tools.assess_solar_conditions(capacity_kw=0)
