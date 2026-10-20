"""Safe, offline configuration preflight for SolarIQ."""

import sys

from pydantic import ValidationError

from config import get_settings


def main() -> int:
    """Validate required settings without making network calls."""
    try:
        settings = get_settings()
    except ValidationError as exc:
        # Print field names and error types only; never echo input values.
        details = [
            f"{'.'.join(str(part) for part in error['loc'])}: {error['type']}"
            for error in exc.errors()
        ]
        print("SolarIQ configuration is invalid.")
        for detail in details:
            print(f"- {detail}")
        return 1

    print("SolarIQ configuration is valid.")
    print(f"Model configured: {settings.solariq_model}")
    print(f"OpenAI API key configured: {'yes' if settings.openai_api_key else 'no'}")
    print("No network requests were made.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
