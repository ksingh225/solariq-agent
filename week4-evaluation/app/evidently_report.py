"""Create separate Evidently reports from SolarIQ evaluation results."""

from pathlib import Path
from typing import Any

import pandas as pd
from evidently import Report
from evidently.presets import DataSummaryPreset


def build_evaluation_dataframe(
    report: dict[str, Any],
) -> pd.DataFrame:
    """Convert a SolarIQ evaluation report into one row per scenario."""
    rows = []

    for result in report.get("results", []):
        checks = result.get("checks", {})
        failed_checks = [
            name for name, passed in checks.items() if not passed
        ]

        judge = result.get("llm_judge")
        judge_score = (
            judge.get("overall_score")
            if isinstance(judge, dict)
            else None
        )
        judge_review = (
            judge.get("needs_human_review")
            if isinstance(judge, dict)
            else None
        )

        rows.append(
            {
                "scenario_id": str(result.get("id", "unknown")),
                "scenario": str(result.get("scenario", "unknown")),
                "status": str(result.get("status", "unknown")),
                "deterministic_score": float(result.get("score", 0.0)),
                "deterministic_checks_total": int(
                    result.get("total_checks", len(checks))
                ),
                "deterministic_checks_passed": int(
                    result.get("passed_checks", 0)
                ),
                "deterministic_safety_failure": any(
                    "risk" in name.lower()
                    or "approval" in name.lower()
                    or "control_physical_equipment" in name.lower()
                    for name in failed_checks
                ),
                "failed_check_count": len(failed_checks),
                "llm_judge_score": (
                    float(judge_score) if judge_score is not None else None
                ),
                "llm_judge_needs_review": (
                    bool(judge_review) if judge_review is not None else None
                ),
                "evaluation_error": bool(result.get("error")),
            }
        )

    if not rows:
        raise ValueError(
            "No scenario results found in the evaluation report."
        )

    return pd.DataFrame(rows)


def generate_evidently_report(
    evaluation_report: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, str]:
    """Write HTML and JSON monitoring reports without modifying the source."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    dataframe = build_evaluation_dataframe(evaluation_report)

    snapshot = Report(
        metrics=[DataSummaryPreset()],
        metadata={
            "project": "SolarIQ",
            "report_type": "evaluation_monitoring",
        },
        tags=["solariq", "evaluation"],
    ).run(dataframe)

    html_path = output_path / "evidently_evaluation_report.html"
    json_path = output_path / "evidently_evaluation_report.json"

    snapshot.save_html(str(html_path))
    snapshot.save_json(str(json_path))

    return {
        "html": str(html_path),
        "json": str(json_path),
        "scenario_count": str(len(dataframe)),
    }
