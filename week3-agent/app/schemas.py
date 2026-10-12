from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Evidence(BaseModel):
    description: str = Field(min_length=1)
    source: str = Field(min_length=1)
    evidence_type: Literal["observed", "estimated", "documented"]


class RootCauseHypothesis(BaseModel):
    cause: str = Field(min_length=1)
    reasoning: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    action: str = Field(min_length=1)
    risk_level: Literal["low", "medium", "high", "critical"]
    requires_human_approval: bool

    @model_validator(mode="after")
    def enforce_human_approval(self):
        """Require human approval for high- and critical-risk actions."""
        if (
            self.risk_level in ("high", "critical")
            and not self.requires_human_approval
        ):
            raise ValueError(
                "High- and critical-risk recommendations require human approval."
            )
        return self


class SolarAssessment(BaseModel):
    summary: str = Field(min_length=1)
    evidence: list[Evidence] = Field(default_factory=list)
    root_cause_hypotheses: list[RootCauseHypothesis] = Field(
        default_factory=list
    )
    recommendations: list[Recommendation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)