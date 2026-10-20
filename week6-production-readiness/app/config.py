"""Validated configuration for the SolarIQ Week 6 hardening layer."""

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SolarIQSettings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        case_sensitive=True,
    )

    solariq_model: str = Field(
        validation_alias="SOLARIQ_MODEL",
        min_length=1,
        description="Explicit Pydantic AI model identifier.",
    )
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
        repr=False,
    )

    @field_validator("solariq_model")
    @classmethod
    def validate_model_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("SOLARIQ_MODEL must not be empty.")
        if value.lower() == "test":
            raise ValueError(
                "SOLARIQ_MODEL='test' is reserved for tests; "
                "configure a real model explicitly."
            )
        return value


@lru_cache(maxsize=1)
def get_settings() -> SolarIQSettings:
    """Return cached settings from the process environment."""
    return SolarIQSettings()
