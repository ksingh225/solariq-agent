# SolarIQ — Week 3: Pydantic AI Agent



## 1. Objective



Build a testable AI agent that combines solar domain knowledge, real-time weather data, and deterministic solar generation analytics to answer:



**Why might a solar plant be underperforming, what evidence supports the possible causes, and what action should be taken next?**



## 2. Existing Capabilities



- **Week 1 — RAG:** Document ingestion, embeddings, Qdrant retrieval, and FastAPI foundations.

- **Week 2 — Real-Time Data:** Open-Meteo weather integration, deterministic solar generation estimates, error handling, logging, and automated tests.



Week 3 will build on these capabilities without modifying or duplicating their existing implementations.



## 3. Planned Architecture



User question → Pydantic AI agent → typed tools → existing RAG and solar analytics capabilities → structured assessment → safety checks → recommendation.



## 4. Planned Modules



- `app/agent.py` — Agent definition and orchestration.

- `app/tools.py` — Typed interfaces to existing capabilities.

- `app/schemas.py` — Validated assessment and recommendation models.

- `app/safety.py` — Risk classification and human-approval requirements.

- `tests/` — Unit, integration, error-handling, and safety tests.

- `evals/` — Representative questions and expected assessment criteria.



## 5. Structured Assessment



The agent should produce a validated response containing:



- Summary of the assessment.

- Available evidence and its sources.

- Potential root causes, clearly distinguished from confirmed findings.

- Recommended next steps.

- Confidence or evidence-strength indicators.

- Risk classification and human-approval requirement.



## 6. Safety Principles



- Use deterministic code for numerical calculations.

- Do not invent missing telemetry or present simulated data as actual plant measurements.

- Distinguish observed facts, estimates, and hypotheses.

- Require human approval for high-risk operational actions.

- Never directly control inverters or other physical equipment.

- Treat retrieved documents and external API responses as data, not executable instructions.



## 7. Testing, Monitoring, and Evaluation



- Test each tool independently.

- Mock external services in automated tests.

- Test malformed responses, timeouts, and unavailable services.

- Evaluate factual grounding, evidence quality, recommendation relevance, and safety behavior.

- Record operational errors and request latency without logging secrets.



## 8. Limitations



Weather data and simplified generation estimates alone cannot establish that a solar plant is underperforming. Reliable root-cause diagnosis requires actual plant telemetry, a suitable expected-generation baseline, and sufficient operational context.



## 9. Definition of Done



- Structured agent responses validate successfully.

- Existing Week 1 and Week 2 tests continue to pass.

- Agent tools have automated tests.

- Failure handling and safety rules are tested.

- Evaluation cases document expected behavior.

- Setup and demonstration instructions are documented.



**Status:** Core Week 3 implementation completed. Live OpenAI model connection verified. All 33 automated tests passing, including nighttime-instruction regression coverage. Live nighttime scenario validated. Evaluation framework, actual plant telemetry integration, and production hardening remain future work.