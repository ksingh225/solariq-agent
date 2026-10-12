from typing import Literal

RiskLevel = Literal["low", "medium", "high", "critical"]


def requires_human_approval(risk_level: RiskLevel) -> bool:
    """Require human approval for high-risk operational actions."""
    return risk_level in ("high", "critical")


def validate_action_safety(
    risk_level: RiskLevel,
    requires_approval: bool,
) -> bool:
    """Reject actions that bypass mandatory human approval."""
    if requires_human_approval(risk_level) and not requires_approval:
        return False

    return True