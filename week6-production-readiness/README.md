# SolarIQ — Week 6: Production Readiness

## 1. Objective

Harden SolarIQ into a reliable, testable, production-style proof of concept for solar operations decision support, reusing the completed Weeks 1–5.

## 2. Scope

- Validate configuration and model selection safely.
- Handle missing configuration and external service failures predictably.
- Preserve evidence provenance, timestamps, units, and data-quality limitations.
- Improve structured logging without exposing credentials or sensitive data.
- Test failure scenarios and preserve existing regression behavior.
- Document setup, execution, testing, and known limitations.

## 3. Architecture

Week 6 hardening components initially live in this folder. Existing Weeks 1–5 remain unchanged unless an integration change is shown to be necessary, reviewed, and tested.

## 4. Safety and Data Integrity

- Synthetic telemetry must always be labelled as synthetic.
- Weather-derived output is an estimate, not measured generation.
- Misaligned timestamps must not support unsupported performance conclusions.
- Root-cause hypotheses must be supported by relevant evidence.
- High-risk recommendations require human approval.
- SolarIQ must never directly control physical equipment.
- Secrets must not be logged or committed.

## 5. Implementation Plan

1. Establish the Week 6 baseline and configuration requirements.
2. Implement isolated configuration validation with automated tests.
3. Add reliability and failure-handling checks.
4. Add structured observability and safe error reporting.
5. Run Week 6 tests and the existing regression suite.
6. Document reproducible demonstration steps and limitations.

## 6. Acceptance Criteria

- Invalid or missing required settings produce clear, safe errors.
- No credentials appear in logs or test output.
- Unit tests cover valid, missing, and invalid configuration.
- External service failures do not become fabricated evidence.
- Existing regression tests continue to pass.
- Synthetic and estimated data remain clearly distinguished from measurements.
- Setup, test commands, and limitations are documented.

## 7. Out of Scope

- Direct inverter or plant equipment control.
- Claims of production certification or operational readiness without appropriate deployment, security, and field validation.
- Presenting synthetic telemetry as real plant data.

## 8. Configuration Preflight

Run from the repository root in Git Bash:

```bash
export SOLARIQ_MODEL="openai:gpt-4o-mini"
PYTHONPATH=week6-production-readiness/app \
  python week6-production-readiness/app/preflight.py
```

The preflight validates configuration without making network requests. It reports whether an API key is configured but does not validate the key with the provider.

`SOLARIQ_MODEL` is required. `OPENAI_API_KEY` is optional for this offline configuration check; a successful preflight does not guarantee that a live model call will succeed.

## 9. Tests

Run the Week 6 tests:

```bash
python -m pytest week6-production-readiness/tests/ -q
```

Run the combined regression suite for Weeks 2–6:

```bash
python -m pytest \
  week2-realtime-data/tests/ \
  week3-agent/tests/ \
  week4-evaluation/tests/ \
  week5-e2e-showcase/ \
  week6-production-readiness/tests/ \
  -q
```

Last verified checkpoint before this documentation update:

- Week 6 tests: 14 passed.
- Combined Weeks 2–6 regression suite: 84 passed.

Rerun the commands above after subsequent code changes; these counts describe the previous verified checkpoint, not a test run performed by this README edit.

## 10. Current Status and Limitations

Implemented:

- Isolated configuration validation.
- Offline configuration preflight.
- Validation of non-finite solar analytics inputs.
- Validation of Open-Meteo response structure and required numeric weather fields.

Pending:

- Integration of Week 6 configuration and preflight with the Week 3 agent.
- Broader external-service failure handling.
- Structured observability improvements.
- End-to-end, deployment, security, and field validation.

A passing preflight does not prove that credentials are valid, provider access is available, or the system is production-certified.
