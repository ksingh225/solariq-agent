from pathlib import Path
import importlib.util

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "solar_analytics.py"
)

spec = importlib.util.spec_from_file_location(
    "solar_analytics", MODULE_PATH
)
solar_analytics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solar_analytics)

estimate_solar_generation = solar_analytics.estimate_solar_generation


def test_estimates_solar_power():
    result = estimate_solar_generation(
        capacity_kw=5,
        irradiance_wm2=500,
        efficiency=0.80,
    )

    assert result["estimated_power_kw"] == 2.0
    assert result["model_type"] == "simplified_engineering_estimate"


def test_zero_irradiance_produces_zero_power():
    result = estimate_solar_generation(
        capacity_kw=5,
        irradiance_wm2=0,
    )

    assert result["estimated_power_kw"] == 0.0


def test_caps_irradiance_factor_at_one():
    result = estimate_solar_generation(
        capacity_kw=5,
        irradiance_wm2=1200,
    )

    assert result["estimated_power_kw"] == 4.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"capacity_kw": 0, "irradiance_wm2": 500},
        {"capacity_kw": 5, "irradiance_wm2": -1},
        {"capacity_kw": 5, "irradiance_wm2": 500, "efficiency": 0},
        {"capacity_kw": 5, "irradiance_wm2": 500, "efficiency": 1.1},
    ],
)
def test_rejects_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        estimate_solar_generation(**kwargs)