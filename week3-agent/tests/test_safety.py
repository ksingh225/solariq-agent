import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "week3-agent" / "app"))

from safety import requires_human_approval, validate_action_safety
from schemas import Recommendation


def test_low_risk_does_not_require_approval():
    assert not requires_human_approval("low")


def test_high_risk_requires_approval():
    assert requires_human_approval("high")


def test_critical_action_cannot_bypass_approval():
    assert not validate_action_safety("critical", False)


def test_critical_action_with_approval_passes():
    assert validate_action_safety("critical", True)


def test_low_risk_recommendation_can_skip_approval():
    recommendation = Recommendation(
        action="Review performance report",
        risk_level="low",
        requires_human_approval=False,
    )
    assert recommendation.risk_level == "low"


def test_high_risk_recommendation_requires_approval():
    with pytest.raises(ValidationError):
        Recommendation(
            action="Inspect inverter",
            risk_level="high",
            requires_human_approval=False,
        )


def test_critical_risk_recommendation_requires_approval():
    with pytest.raises(ValidationError):
        Recommendation(
            action="Restart inverter",
            risk_level="critical",
            requires_human_approval=False,
        )