
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


CLIENT_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "weather_client.py"
)

spec = importlib.util.spec_from_file_location(
    "weather_client", CLIENT_PATH
)
weather_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weather_client)


@pytest.mark.asyncio
async def test_fetch_solar_weather_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "latitude": 17.385,
        "longitude": 78.4867,
        "timezone": "Asia/Kolkata",
        "current": {
            "time": "2026-10-10T12:00",
            "temperature_2m": 32.0,
            "cloud_cover": 20,
            "shortwave_radiation": 650.0,
        },
    }
    mock_response.raise_for_status.return_value = None

    with patch.object(
        httpx.AsyncClient, "get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_response

        result = await weather_client.fetch_solar_weather()

    assert result["temperature_c"] == 32.0
    assert result["cloud_cover_percent"] == 20
    assert result["shortwave_radiation_wm2"] == 650.0
    assert result["source"] == "Open-Meteo"


@pytest.mark.asyncio
async def test_fetch_solar_weather_missing_fields():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "current": {
            "time": "2026-10-10T12:00",
            "temperature_2m": 32.0,
        }
    }
    mock_response.raise_for_status.return_value = None

    with patch.object(
        httpx.AsyncClient, "get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Missing current weather fields"):
            await weather_client.fetch_solar_weather()
@pytest.mark.asyncio
async def test_fetch_solar_weather_network_error():
    with patch.object(
        httpx.AsyncClient,
        "get",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("Connection failed"),
    ):
        with pytest.raises(httpx.ConnectError):
            await weather_client.fetch_solar_weather()

@pytest.mark.asyncio
async def test_fetch_solar_weather_timeout():
    with patch.object(
        httpx.AsyncClient,
        "get",
        new_callable=AsyncMock,
        side_effect=httpx.TimeoutException("Request timed out"),
    ):
        with pytest.raises(httpx.TimeoutException):
            await weather_client.fetch_solar_weather()