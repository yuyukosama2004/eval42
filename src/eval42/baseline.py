"""Explicit baseline creation and comparison."""

from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from eval42._version import __version__
from eval42.errors import BaselineError
from eval42.schema import validate_instance
from eval42.util import sha256_value


def baseline_from_report(report: dict[str, Any]) -> dict[str, Any]:
    run = report["run"]
    cases = report["cases"]
    baseline = {
        "schema_version": "1",
        "project_name": run["project_name"],
        "created_at": datetime.now(UTC).isoformat(),
        "dataset": {
            "version": run.get("dataset_version", "unknown"),
            "hash": run["dataset_hash"],
        },
        "run_fingerprint": {
            "target_revision": run["revision"],
            "adapter_version": run.get("adapter_version", "1"),
            "eval42_version": run.get("eval42_version", __version__),
            "config_hash": run["config_hash"],
            "metric_hash": run["metric_hash"],
            "metric_version": run.get("metric_version", "unknown"),
            "environment": run.get("environment", platform.platform()),
        },
        "summary": report["summary"],
        "cases": [
            {
                "case_id": case["case_id"],
                "case_hash": case["case_hash"],
                "status": case["status"],
                "metrics": case.get("metrics", {}),
            }
            for case in cases
        ],
    }
    validate_instance(baseline, "baseline")
    return baseline


def write_baseline(baseline: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output


def load_baseline(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        baseline = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"cannot load baseline {source}: {exc}") from exc
    if not isinstance(baseline, dict):
        raise BaselineError("baseline root must be an object")
    try:
        validate_instance(baseline, "baseline")
    except Exception as exc:
        raise BaselineError(str(exc)) from exc
    return baseline


def compare_report_to_baseline(
    report: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    current_metrics = report["summary"].get("metrics", {})
    baseline_metrics = baseline["summary"].get("metrics", {})
    comparable = sorted(set(current_metrics).intersection(baseline_metrics))
    metric_changes = {
        name: {
            "current": current_metrics[name],
            "baseline": baseline_metrics[name],
            "absolute_change": current_metrics[name] - baseline_metrics[name],
            "relative_change": _relative_change(current_metrics[name], baseline_metrics[name]),
        }
        for name in comparable
        if isinstance(current_metrics[name], (int, float))
        and isinstance(baseline_metrics[name], (int, float))
    }
    baseline_cases = {case["case_id"]: case for case in baseline["cases"]}
    current_cases = {case["case_id"]: case for case in report["cases"]}
    comparable_cases = {
        case_id
        for case_id in set(baseline_cases).intersection(current_cases)
        if baseline_cases[case_id]["case_hash"] == current_cases[case_id]["case_hash"]
    }
    new_errors = sorted(
        case_id
        for case_id in comparable_cases
        if baseline_cases[case_id]["status"] == "completed"
        and current_cases[case_id]["status"] == "error"
    )
    fixed_errors = sorted(
        case_id
        for case_id in comparable_cases
        if baseline_cases[case_id]["status"] == "error"
        and current_cases[case_id]["status"] == "completed"
    )
    return {
        "schema_version": "1",
        "project_name": report["run"]["project_name"],
        "dataset_changed": report["run"]["dataset_hash"] != baseline["dataset"]["hash"],
        "fingerprint_changed": _fingerprint_changes(report, baseline),
        "metric_changes": metric_changes,
        "comparable_case_count": len(comparable_cases),
        "new_errors": new_errors,
        "fixed_errors": fixed_errors,
        "comparison_hash": sha256_value(
            {
                "report": report["run"],
                "baseline": baseline["run_fingerprint"],
            }
        ),
    }


def _relative_change(current: float, baseline: float) -> float | None:
    return None if baseline == 0 else (current - baseline) / abs(baseline)


def _fingerprint_changes(
    report: dict[str, Any],
    baseline: dict[str, Any],
) -> list[str]:
    run = report["run"]
    fingerprint = baseline["run_fingerprint"]
    pairs = {
        "target_revision": (run["revision"], fingerprint["target_revision"]),
        "adapter_version": (run.get("adapter_version"), fingerprint["adapter_version"]),
        "eval42_version": (run.get("eval42_version"), fingerprint["eval42_version"]),
        "config_hash": (run["config_hash"], fingerprint["config_hash"]),
        "metric_hash": (run["metric_hash"], fingerprint["metric_hash"]),
        "metric_version": (
            run.get("metric_version"),
            fingerprint.get("metric_version"),
        ),
        "environment": (run.get("environment"), fingerprint["environment"]),
    }
    return [name for name, (current, previous) in pairs.items() if current != previous]
