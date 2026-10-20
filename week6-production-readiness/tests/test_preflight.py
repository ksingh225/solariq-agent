"""Integration tests for the offline SolarIQ configuration preflight."""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = REPO_ROOT / "week6-production-readiness" / "app"
PREFLIGHT = APP_DIR / "preflight.py"


def run_preflight(extra_env=None):
    env = os.environ.copy()
    env.pop("SOLARIQ_MODEL", None)
    env.pop("OPENAI_API_KEY", None)
    env["PYTHONPATH"] = str(APP_DIR)

    if extra_env:
        env.update(extra_env)

    return subprocess.run(
        [sys.executable, str(PREFLIGHT)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_preflight_accepts_valid_model_without_api_key():
    result = run_preflight({"SOLARIQ_MODEL": "openai:gpt-4o-mini"})

    assert result.returncode == 0
    assert "SolarIQ configuration is valid." in result.stdout
    assert "OpenAI API key configured: no" in result.stdout
    assert "No network requests were made." in result.stdout


def test_preflight_rejects_missing_model():
    result = run_preflight()

    assert result.returncode == 1
    assert "SolarIQ configuration is invalid." in result.stdout
    assert "SOLARIQ_MODEL" in result.stdout
    assert "example-secret-value" not in result.stdout + result.stderr


def test_preflight_rejects_reserved_test_model():
    result = run_preflight({"SOLARIQ_MODEL": "test"})

    assert result.returncode == 1
    assert "SolarIQ configuration is invalid." in result.stdout


def test_preflight_does_not_print_api_key_on_validation_failure():
    secret = "example-secret-value"
    result = run_preflight({
        "SOLARIQ_MODEL": "test",
        "OPENAI_API_KEY": secret,
    })

    assert result.returncode == 1
    assert secret not in result.stdout
    assert secret not in result.stderr
