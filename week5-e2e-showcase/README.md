# SolarIQ — Week 5: End-to-End Showcase



## Objective



Demonstrate an end-to-end SolarIQ workflow that combines simulated solar-plant telemetry, weather data, simplified expected-generation estimates, and the existing SolarIQ agent to produce structured, evidence-grounded assessments.



## Scope



- Introduce clearly labelled simulated solar-plant telemetry.

- Reuse existing agent tools and schemas wherever possible.

- Combine telemetry, Open-Meteo weather observations, simplified generation estimates, and available knowledge.

- Produce structured assessments and cautious recommendations.

- Demonstrate normal operation, potential output gaps, and missing telemetry.

- Include automated tests for telemetry, workflow assembly, and agent-runner behaviour.



## Data Integrity



No live solar plant or inverter telemetry is currently available. Simulated readings are for demonstration only and must never be presented as real plant observations.



Weather data, when retrieved, comes from Open-Meteo. Weather observation timestamps must be interpreted using the timezone returned by the weather source; they must not automatically be labelled UTC.



Expected-generation values are simplified estimates, not measured output or a validated plant-performance benchmark. A difference between simulated output and an estimate does not, by itself, establish underperformance or its root cause.



## Prerequisites



- Python and the repository virtual environment.

- Dependencies installed from the repository's `requirements.txt`.

- Any model credentials required by the existing SolarIQ agent for live agent runs.



## Run the Showcase



From the repository root, activate the virtual environment and run:



### Offline demonstration



```bash

python week5-e2e-showcase/app/main.py --scenario potential\_output\_gap --capacity-kw 100 --offline

```



### Demonstration with weather retrieval



```bash

python week5-e2e-showcase/app/main.py --scenario potential\_output\_gap --capacity-kw 100

```



### Other scenarios



Replace `potential\_output\_gap` with `normal` or `missing` to demonstrate the other telemetry scenarios.



Use `--help` to view the available command-line options.



## Tests



Run the Week 5 tests:



```bash

python -m pytest week5-e2e-showcase/tests -q

```



Run the broader Week 3, Week 4, and Week 5 regression tests:



```bash

python -m pytest week3-agent/tests week4-evaluation/tests week5-e2e-showcase/tests -q

```



## Current Limitations



- Plant and inverter telemetry is simulated.

- Expected generation uses a simplified calculation.

- Weather retrieval depends on external service availability.

- Results depend on the existing agent and its configured model.

- The showcase does not establish a production-ready, real-time plant-monitoring integration.



## Acceptance Criteria



- A repeatable workflow runs from a business question to a structured assessment.

- Simulated observations, external weather data, estimates, and hypotheses are distinguished.

- Missing data leads to cautious conclusions rather than invented diagnoses.

- Automated tests cover the principal demonstration scenarios.

- Setup, execution, and limitations are documented.



## Status



The Week 5 offline demonstration has been validated end to end. In offline mode, the assessment identifies plant telemetry as simulated, excludes missing weather from evidence, avoids unsupported root-cause claims, and states that no weather-based expected-output estimate was calculated.

Validation results:
- Week 5 tests: 27 passed.
- Combined Week 3, Week 4, and Week 5 regression tests: 97 passed.
- Offline `potential_output_gap` CLI scenario: completed successfully.

The combined regression run emitted 10 dependency deprecation warnings and had no test failures.

Limitations remain: telemetry is simulated, expected-generation estimates are simplified, weather retrieval depends on an external service, and this showcase does not establish a production-ready plant-monitoring integration.
