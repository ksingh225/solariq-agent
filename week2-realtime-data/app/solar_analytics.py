"""Simplified solar generation analytics."""

def estimate_solar_generation(
    capacity_kw: float,
    irradiance_wm2: float,
    efficiency: float = 0.80,
) -> dict:
    """Estimate instantaneous solar output using irradiance and efficiency.

    This is a simplified engineering estimate, not a certified forecast.
    """
    if capacity_kw <= 0:
        raise ValueError("capacity_kw must be greater than zero")

    if irradiance_wm2 < 0:
        raise ValueError("irradiance_wm2 cannot be negative")

    if not 0 < efficiency <= 1:
        raise ValueError("efficiency must be greater than 0 and at most 1")

    irradiance_factor = min(irradiance_wm2 / 1000.0, 1.0)
    estimated_power_kw = capacity_kw * irradiance_factor * efficiency

    return {
        "capacity_kw": capacity_kw,
        "irradiance_wm2": irradiance_wm2,
        "efficiency": efficiency,
        "estimated_power_kw": round(estimated_power_kw, 3),
        "model_type": "simplified_engineering_estimate",
    }