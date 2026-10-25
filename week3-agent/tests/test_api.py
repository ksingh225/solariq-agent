import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
for path in (
    ROOT,
    ROOT / "week2-realtime-data" / "app",
    ROOT / "week3-agent" / "app",
):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import api


client = TestClient(api.app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "SolarIQ",
        "version": "0.1.0",
    }


def test_assess_rejects_blank_question():
    response = client.post(
        "/assess",
        json={"question": "   "},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Question must not be blank."


def test_assess_rejects_missing_question():
    response = client.post("/assess", json={})

    assert response.status_code == 422


def test_assess_returns_structured_agent_output(monkeypatch):
    expected = {
        "summary": "Zero generation at night alone does not indicate a fault.",
        "evidence": [],
        "root_cause_hypotheses": [],
        "recommendations": [],
        "limitations": ["Daytime generation data is needed."],
    }

    class FakeOutput:
        def model_dump(self, mode="python"):
            return expected

    class FakeResult:
        output = FakeOutput()

    async def fake_run(question, deps):
        assert question == "Assess nighttime zero generation."
        assert isinstance(deps, api.SolarAgentDeps)
        return FakeResult()

    monkeypatch.setattr(api.solar_agent, "run", fake_run)

    response = client.post(
        "/assess",
        json={"question": "Assess nighttime zero generation."},
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_assess_returns_safe_error_when_agent_fails(monkeypatch):
    async def failing_run(question, deps):
        raise RuntimeError("Internal test failure")

    monkeypatch.setattr(api.solar_agent, "run", failing_run)

    response = client.post(
        "/assess",
        json={"question": "Assess solar performance."},
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": (
            "SolarIQ could not complete the assessment. "
            "Check server logs."
        )
    }
