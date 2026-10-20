import asyncio
import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError


APP_DIR = Path(__file__).resolve().parents[1] / "app"
SPEC = importlib.util.spec_from_file_location(
    "solariq_week5_showcase", APP_DIR / "showcase.py"
)
showcase = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(showcase)


def test_normal_scenario_builds_explicitly_simulated_inputs():
    result = asyncio.run(
        showcase.build_showcase_inputs(
            scenario="normal",
            capacity_kw=100,
            fetch_weather=False,
        )
    )

    assert result.capacity_kw == 100
    assert result.simulated_telemetry["is_simulated"] is True
    assert result.simulated_telemetry["source"] == "simulated"
    assert result.simulated_telemetry["measured_power_kw"] == 60
    assert result.weather is None
    assert result.expected_output_estimate is None
    assert any("simulated" in item.lower() for item in result.limitations)


def test_missing_scenario_does_not_invent_measured_generation():
    result = asyncio.run(
        showcase.build_showcase_inputs(
            scenario="missing",
            capacity_kw=100,
            fetch_weather=False,
        )
    )

    assert result.simulated_telemetry["measured_power_kw"] is None
    assert result.simulated_telemetry["inverter_status"] is None
    assert result.expected_output_estimate is None


def test_potential_output_gap_is_not_presented_as_a_confirmed_fault():
    result = asyncio.run(
        showcase.build_showcase_inputs(
            scenario="potential_output_gap",
            capacity_kw=100,
            fetch_weather=False,
        )
    )

    assert result.simulated_telemetry["measured_power_kw"] == 25
    assert any(
        "does not establish its cause" in item
        for item in result.limitations
    )


def test_invalid_capacity_is_rejected():
    with pytest.raises(ValidationError):
        asyncio.run(
            showcase.build_showcase_inputs(
                scenario="normal",
                capacity_kw=0,
                fetch_weather=False,
            )
        )


@pytest.mark.asyncio
async def test_weather_and_estimate_are_combined(monkeypatch):
    async def fake_weather():
        return {
            "observed_at": "2026-10-19T10:00",
            "shortwave_radiation_wm2": 700,
            "temperature_c": 30,
            "cloud_cover_percent": 20,
            "source": "Open-Meteo",
        }

    monkeypatch.setattr(
        "weather_client.fetch_solar_weather",
        fake_weather,
    )

    result = await showcase.build_showcase_inputs(
        scenario="normal",
        capacity_kw=100,
        fetch_weather=True,
    )

    assert result.weather["source"] == "Open-Meteo"
    assert result.expected_output_estimate["estimated_power_kw"] == 56
    assert any(
        "irradiance proxy" in item for item in result.limitations
    )


def test_time_alignment_accepts_observations_within_tolerance():
    result = showcase.assess_time_alignment(
        {"observed_at": "2026-10-19T04:40:00+00:00"},
        {
            "observed_at": "2026-10-19T10:00:00",
            "timezone": "Asia/Kolkata",
        },
    )

    assert result["aligned"] is True
    assert result["status"] == "aligned"
    assert result["difference_minutes"] == 10


def test_time_alignment_rejects_observations_outside_tolerance():
    result = showcase.assess_time_alignment(
        {"observed_at": "2026-10-19T10:30:00+00:00"},
        {
            "observed_at": "2026-10-19T10:00:00",
            "timezone": "Asia/Kolkata",
        },
    )

    assert result["aligned"] is False
    assert result["status"] == "not_aligned"
    assert result["difference_minutes"] == 360.0


def test_time_alignment_rejects_telemetry_without_timezone():
    result = showcase.assess_time_alignment(
        {"observed_at": "2026-10-19T10:00:00"},
        {
            "observed_at": "2026-10-19T15:30:00",
            "timezone": "Asia/Kolkata",
        },
    )

    assert result["aligned"] is False
    assert result["status"] == "telemetry_timezone_missing"


def test_time_alignment_handles_missing_weather():
    result = showcase.assess_time_alignment(
        {"observed_at": "2026-10-19T10:00:00+00:00"},
        None,
    )

    assert result["aligned"] is False
    assert result["status"] == "weather_unavailable"


def test_time_alignment_rejects_invalid_timezone():
    result = showcase.assess_time_alignment(
        {"observed_at": "2026-10-19T10:00:00+00:00"},
        {
            "observed_at": "2026-10-19T10:00:00",
            "timezone": "Invalid/Timezone",
        },
    )

    assert result["aligned"] is False
    assert result["status"] == "invalid_timestamp_or_timezone"
