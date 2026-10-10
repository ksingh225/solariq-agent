
# SolarIQ — Week 2: Real-Time Data and Solar Analytics

## 1. Objective

Extend the Week 1 RAG foundation with live weather and solar irradiance data, deterministic solar power estimation, and a combined solar assessment service.

Week 2 is implemented in a separate folder to keep the Week 1 implementation unchanged.

## 2. Architecture

```text
Open-Meteo API
      |
      v
Weather Client
      |
      v
Validated Weather Data
      |
      v
Solar Analytics
      |
      v
Integrated Solar Assessment
      |
      v
Structured Result
```

The weather client retrieves current conditions. The analytics module calculates a simplified instantaneous power estimate. The service combines both outputs into one assessment.

## 3. Implemented Components

### 3.1 Open-Meteo Weather Client

File: `app/weather_client.py`

- Makes asynchronous HTTP requests using `httpx`.
- Uses Hyderabad, India as the default location.
- Retrieves temperature, cloud cover, and shortwave radiation.
- Validates required response fields.
- Configures a 15-second HTTP timeout.
- Logs request duration and API or validation failures.
- Includes the observation timestamp, coordinates, timezone, and source attribution.

### 3.2 Solar Analytics

File: `app/solar_analytics.py`

- Estimates instantaneous solar power from installed capacity, irradiance, and efficiency.
- Validates capacity, irradiance, and efficiency inputs.
- Caps the irradiance factor at 1.0.

Simplified calculation:

`estimated_power_kw = capacity_kw * min(irradiance_wm2 / 1000, 1.0) * efficiency`

Example: A 5 kW system at 500 W/m² irradiance and 80% efficiency produces an estimated instantaneous output of 2 kW.

This is an engineering approximation, not a certified production forecast. It does not model all plant-specific losses, temperature effects, shading, inverter limits, or historical performance.

### 3.3 Integrated Solar Assessment

File: `app/solar_service.py`

Combines the weather client and solar analytics into one result containing:

- Location and timezone
- Weather observation timestamp
- Temperature, cloud cover, and shortwave radiation
- Weather data source
- Estimated instantaneous power in kW
- Assessment type identifying the result as a simplified estimate

The service propagates weather API errors rather than silently hiding them.

## 4. Project Structure

```text
week2-realtime-data/
├── README.md
├── app/
│   ├── __init__.py
│   ├── weather_client.py
│   ├── solar_analytics.py
│   └── solar_service.py
└── tests/
    ├── test_weather_client.py
    ├── test_solar_analytics.py
    └── test_solar_service.py
```

## 5. Testing

Run all Week 1 and Week 2 tests from the repository root:

```bash
python -m pytest tests/unit week2-realtime-data/tests -v
```

Latest recorded result: **18 tests passed**.

### Week 1 — RAG Foundation

- 5 tests passed.

### Week 2 — Weather Client

- Successful API response
- Missing required fields
- Network connection error
- Timeout exception

**4 tests passed.**

### Week 2 — Solar Analytics

- Normal power estimation
- Zero irradiance
- Irradiance factor capping
- Invalid capacity, irradiance, and efficiency inputs

**7 tests passed.**

### Week 2 — Integrated Service

- Combines weather data with the solar power estimate
- Propagates weather API errors

**2 tests passed.**

The weather and service tests use mocked responses where appropriate, so they do not depend on live API availability for every test run.

## 6. Monitoring and Error Handling

Current capabilities:

- HTTP request timeout configuration
- Request-duration logging
- API and validation exception logging
- Automated tests for network failures and timeouts

Further improvements are planned for structured logs, API response metrics, retries, and operational monitoring.

## 7. Operational and Safety Principles

- Keep the Week 1 RAG implementation unchanged.
- Separate API retrieval from deterministic calculations.
- Preserve observation timestamps and source attribution.
- Distinguish API observations from calculated estimates.
- Do not interpret zero irradiance at night as evidence of a plant fault.
- Do not present the simplified calculation as a certified forecast.
- Do not directly control physical solar equipment.
- Require human review for future high-risk operational recommendations.

## 8. Known Limitations

- Hyderabad is the default location; location configuration needs further refinement.
- The power estimate is simplified and does not include every plant-specific loss.
- Actual plant telemetry and measured generation are not yet integrated.
- Historical baseline comparison and underperformance diagnosis are not implemented.
- Structured operational metrics and advanced evaluation scenarios remain future work.

## 9. Remaining Work

- Improve API response validation, types, ranges, and units.
- Add retry policies for suitable transient failures.
- Improve structured logging and request-duration monitoring.
- Expose the assessment through a clean application interface.
- Evaluate daylight, nighttime, low-irradiance, and API-failure scenarios.
- Document reproducible environment setup and configuration.
- Integrate with the future AI agent only after the service behavior is evaluated.

## 10. Status

**In progress.**

The weather client, solar analytics, integrated assessment, initial monitoring, and automated tests are implemented. The latest combined regression run passed all 18 Week 1 and Week 2 tests. Additional monitoring, evaluation, and robustness work remains.
