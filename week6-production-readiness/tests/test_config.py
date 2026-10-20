"""Tests for isolated SolarIQ configuration validation."""

import importlib.util
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

CONFIG_PATH = Path(__file__).resolve().parents[1] / "app" / "config.py"
SPEC = importlib.util.spec_from_file_location("solariq_week6_config", CONFIG_PATH)
CONFIG_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CONFIG_MODULE
SPEC.loader.exec_module(CONFIG_MODULE)

SolarIQSettings = CONFIG_MODULE.SolarIQSettings
get_settings = CONFIG_MODULE.get_settings


def test_accepts_explicit_model_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = SolarIQSettings(SOLARIQ_MODEL="openai:gpt-4o-mini")

    assert settings.solariq_model == "openai:gpt-4o-mini"
    assert settings.openai_api_key is None


def test_strips_whitespace_from_model_name():
    settings = SolarIQSettings(SOLARIQ_MODEL="  openai:gpt-4o-mini  ")

    assert settings.solariq_model == "openai:gpt-4o-mini"


@pytest.mark.parametrize("model_name", ["", "   ", "test", "TEST"])
def test_rejects_empty_or_test_model_names(model_name):
    with pytest.raises(ValidationError):
        SolarIQSettings(SOLARIQ_MODEL=model_name)


def test_missing_model_is_rejected_even_if_api_key_exists(monkeypatch):
    monkeypatch.delenv("SOLARIQ_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "example-secret-value")

    with pytest.raises(ValidationError):
        SolarIQSettings()


def test_api_key_is_masked_in_representation():
    settings = SolarIQSettings(
        SOLARIQ_MODEL="openai:gpt-4o-mini",
        OPENAI_API_KEY="example-secret-value",
    )

    assert "example-secret-value" not in repr(settings)
    assert settings.openai_api_key is not None
    assert settings.openai_api_key.get_secret_value() == "example-secret-value"


def test_get_settings_uses_process_environment(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("SOLARIQ_MODEL", "openai:gpt-4o-mini")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    try:
        settings = get_settings()
        assert settings.solariq_model == "openai:gpt-4o-mini"
        assert settings.openai_api_key is None
    finally:
        get_settings.cache_clear()


def test_get_settings_returns_cached_instance(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("SOLARIQ_MODEL", "openai:gpt-4o-mini")

    try:
        first = get_settings()
        second = get_settings()
        assert first is second
    finally:
        get_settings.cache_clear()
