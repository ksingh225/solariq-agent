"""Deterministic simulated solar-plant telemetry for the Week 5 showcase.

These readings are synthetic demonstration data, not measurements from
a real solar plant or inverter.
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator


TelemetryScenario = Literal["normal", "potential_output_gap", "missing"]


class SimulatedTelemetry(BaseModel):
    """A validated, explicitly labelled simulated telemetry record."""

    plant_id: str = Field(min_length=1)
    capacity_kw: float = Field(gt=0)
    observed_at: datetime
    measured_power_kw: float | None = Field(default=None, ge=0)
    inverter_status: str | None = None
    source: Literal["simulated"] = "simulated"
    is_simulated: Literal[True] = True

    @model_validator(mode="after")
    def validate_measurement(self):
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must include a timezone")
        if self.measured_power_kw is not None:
            if self.measured_power_kw > self.capacity_kw:
                raise ValueError(
                    "measured_power_kw cannot exceed configured capacity"
                )
        return self


def get_simulated_telemetry(
    scenario: TelemetryScenario,
    capacity_kw: float,
    plant_id: str = "SOLARIQ-DEMO-01",
) -> SimulatedTelemetry:
    """Return deterministic sample telemetry for a showcase scenario.

    The timestamp is fixed to make tests and demonstrations reproducible.
    """
    observed_at = datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)

    if scenario == "normal":
        measured_power_kw = round(capacity_kw * 0.60, 3)
        inverter_status = "simulated_normal"
    elif scenario == "potential_output_gap":
        measured_power_kw = round(capacity_kw * 0.25, 3)
        inverter_status = "simulated_status_unknown"
    elif scenario == "missing":
        measured_power_kw = None
        inverter_status = None
    else:
        raise ValueError(f"Unsupported telemetry scenario: {scenario}")

    return SimulatedTelemetry(
        plant_id=plant_id,
        capacity_kw=capacity_kw,
        observed_at=observed_at,
        measured_power_kw=measured_power_kw,
        inverter_status=inverter_status,
    )
