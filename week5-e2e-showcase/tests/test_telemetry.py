import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "app" / "telemetry.py"
)
SPEC = importlib.util.spec_from_file_location(
    "solariq_week5_telemetry", MODULE_PATH
)
telemetry = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(telemetry)


def test_normal_scenario_is_explicitly_simulated():
    record = telemetry.get_simulated_telemetry("normal", capacity_kw=100)

    assert record.is_simulated is True
    assert record.source == "simulated"
    assert record.capacity_kw == 100
    assert record.measured_power_kw == 60
    assert record.inverter_status == "simulated_normal"


def test_potential_output_gap_scenario():
    record = telemetry.get_simulated_telemetry(
        "potential_output_gap", capacity_kw=100
    )

    assert record.measured_power_kw == 25
    assert record.inverter_status == "simulated_status_unknown"
    assert record.source == "simulated"


def test_missing_scenario_has_no_measured_generation():
    record = telemetry.get_simulated_telemetry("missing", capacity_kw=100)

    assert record.measured_power_kw is None
    assert record.inverter_status is None
    assert record.is_simulated is True


def test_capacity_must_be_positive():
    with pytest.raises(ValidationError):
        telemetry.get_simulated_telemetry("normal", capacity_kw=0)


def test_measurement_cannot_exceed_capacity():
    with pytest.raises(ValidationError):
        telemetry.SimulatedTelemetry(
            plant_id="TEST",
            capacity_kw=10,
            observed_at="2026-10-19T10:00:00+00:00",
            measured_power_kw=11,
        )


def test_timestamp_must_include_timezone():
    with pytest.raises(ValidationError):
        telemetry.SimulatedTelemetry(
            plant_id="TEST",
            capacity_kw=10,
            observed_at="2026-10-19T10:00:00",
            measured_power_kw=5,
        )


def test_unsupported_scenario_is_rejected():
    with pytest.raises(ValueError, match="Unsupported telemetry scenario"):
        telemetry.get_simulated_telemetry("unexpected", capacity_kw=100)
