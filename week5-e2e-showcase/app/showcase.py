
"""Assemble inputs for the SolarIQ Week 5 end-to-end showcase."""

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field


REPO_ROOT = Path(__file__).resolve().parents[2]
WEEK2_APP = REPO_ROOT / "week2-realtime-data" / "app"

for entry in (str(REPO_ROOT), str(WEEK2_APP)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

ALIGNMENT_TOLERANCE_MINUTES = 15


def _load_telemetry_module():
    module_path = Path(__file__).with_name("telemetry.py")
    spec = importlib.util.spec_from_file_location(
        "solariq_week5_telemetry", module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load telemetry module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


telemetry = _load_telemetry_module()


class ShowcaseInputs(BaseModel):
    """Explicitly separated inputs for the decision-support assessment."""

    scenario: str
    plant_id: str
    capacity_kw: float = Field(gt=0)
    simulated_telemetry: dict[str, Any]
    weather: dict[str, Any] | None = None
    expected_output_estimate: dict[str, Any] | None = None
    time_alignment: dict[str, Any]
    limitations: list[str] = Field(default_factory=list)


def assess_time_alignment(
    telemetry_record: dict[str, Any],
    weather: dict[str, Any] | None,
    tolerance_minutes: int = ALIGNMENT_TOLERANCE_MINUTES,
) -> dict[str, Any]:
    """Compare telemetry and weather instants without assuming a timezone."""
    result: dict[str, Any] = {
        "aligned": False,
        "tolerance_minutes": tolerance_minutes,
        "difference_minutes": None,
        "status": "not_comparable",
        "reason": "",
    }

    if tolerance_minutes < 0:
        result["reason"] = "Alignment tolerance cannot be negative."
        return result

    if not weather:
        result["status"] = "weather_unavailable"
        result["reason"] = "No weather observation is available."
        return result

    telemetry_time = telemetry_record.get("observed_at")
    weather_time = weather.get("observed_at")
    weather_timezone = weather.get("timezone")

    if not telemetry_time or not weather_time or not weather_timezone:
        result["status"] = "timestamp_or_timezone_missing"
        result["reason"] = (
            "Both timestamps and the weather timezone are required "
            "to assess time alignment."
        )
        return result

    try:
        plant_dt = datetime.fromisoformat(str(telemetry_time))
        weather_dt = datetime.fromisoformat(str(weather_time))
        zone = ZoneInfo(str(weather_timezone))
    except (ValueError, TypeError, ZoneInfoNotFoundError):
        result["status"] = "invalid_timestamp_or_timezone"
        result["reason"] = "A timestamp or timezone could not be interpreted."
        return result

    # Telemetry timestamps must identify an unambiguous instant.
    if plant_dt.tzinfo is None:
        result["status"] = "telemetry_timezone_missing"
        result["reason"] = "The telemetry timestamp has no timezone."
        return result

    # Open-Meteo can return local wall time without a UTC offset.
    if weather_dt.tzinfo is None:
        weather_dt = weather_dt.replace(tzinfo=zone)

    difference = abs(
        (
            plant_dt.astimezone(timezone.utc)
            - weather_dt.astimezone(timezone.utc)
        ).total_seconds()
    ) / 60

    result["difference_minutes"] = round(difference, 2)
    result["aligned"] = difference <= tolerance_minutes
    result["status"] = "aligned" if result["aligned"] else "not_aligned"
    result["reason"] = (
        "Observation timestamps are within the configured tolerance."
        if result["aligned"]
        else (
            "Observation timestamps exceed the configured tolerance; "
            "do not compare them as synchronized measurements."
        )
    )
    return result


async def build_showcase_inputs(
    scenario: str,
    capacity_kw: float,
    plant_id: str = "SOLARIQ-DEMO-01",
    fetch_weather: bool = True,
) -> ShowcaseInputs:
    """Build a reproducible input bundle without invoking the LLM."""
    record = telemetry.get_simulated_telemetry(
        scenario=scenario,
        capacity_kw=capacity_kw,
        plant_id=plant_id,
    )

    limitations = [
        "Plant telemetry is simulated demonstration data, not real plant data.",
        "The expected output is a simplified estimate, not a certified forecast.",
        "A measured-versus-estimated gap alone does not establish its cause.",
    ]

    weather = None
    estimate = None

    if fetch_weather:
        from solar_analytics import estimate_solar_generation
        from weather_client import fetch_solar_weather

        weather = await fetch_solar_weather()
        irradiance = weather["shortwave_radiation_wm2"]
        estimate = estimate_solar_generation(
            capacity_kw=capacity_kw,
            irradiance_wm2=irradiance,
        )
        limitations.append(
            "Weather-based expected output uses current shortwave radiation "
            "as an irradiance proxy and assumes 0.80 efficiency."
        )
    else:
        limitations.append(
            "Weather retrieval was disabled; no expected-output estimate "
            "was calculated."
        )

    telemetry_data = record.model_dump(mode="json")
    alignment = assess_time_alignment(telemetry_data, weather)

    if weather is not None and not alignment["aligned"]:
        limitations.append(
            "The weather and simulated telemetry timestamps are not confirmed "
            "to be aligned; do not interpret their values as a synchronized "
            "performance comparison."
        )

    return ShowcaseInputs(
        scenario=scenario,
        plant_id=plant_id,
        capacity_kw=capacity_kw,
        simulated_telemetry=telemetry_data,
        weather=weather,
        expected_output_estimate=estimate,
        time_alignment=alignment,
        limitations=limitations,
    )
