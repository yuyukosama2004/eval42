from __future__ import annotations

import copy
from pathlib import Path

import pytest

from eval42.baseline import (
    baseline_from_report,
    compare_report_to_baseline,
    load_baseline,
    write_baseline,
)
from eval42.config import load_config
from eval42.errors import BaselineError, ReportError
from eval42.reporters import load_report, render_markdown, write_reports
from eval42.runner import run_evaluation

from .conftest import ROOT


def _report() -> dict[str, object]:
    return run_evaluation(
        load_config(ROOT / "examples/mock-shopping/eval.yml"),
        write_output=False,
    ).report


def test_baseline_round_trip_and_compare(tmp_path: Path) -> None:
    report = _report()
    baseline = baseline_from_report(report)
    assert baseline["run_fingerprint"]["eval42_version"] == "0.1.0a1"
    assert baseline["run_fingerprint"]["metric_version"] == "1"
    path = write_baseline(baseline, tmp_path / "baseline.json")
    loaded = load_baseline(path)
    comparison = compare_report_to_baseline(report, loaded)
    assert comparison["dataset_changed"] is False
    assert comparison["comparable_case_count"] == 3
    assert comparison["fingerprint_changed"] == []
    assert not comparison["new_errors"]
    changed = copy.deepcopy(report)
    changed["run"]["dataset_hash"] = f"sha256:{'f' * 64}"
    assert compare_report_to_baseline(changed, loaded)["dataset_changed"] is True


def test_baseline_errors(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    with pytest.raises(BaselineError):
        load_baseline(missing)
    invalid = tmp_path / "invalid.json"
    invalid.write_text("[]", encoding="utf-8")
    with pytest.raises(BaselineError, match="root"):
        load_baseline(invalid)


def test_report_round_trip_and_markdown(tmp_path: Path) -> None:
    report = _report()
    paths = write_reports(report, tmp_path, ["json", "markdown"])
    assert load_report(paths["json"])["summary"]["gate"] == "pass"
    markdown = render_markdown(report)
    assert "## Metrics" in markdown
    assert "Execution errors" in markdown
    assert "Case diagnostics" in markdown
    with pytest.raises(ReportError, match="unsupported"):
        write_reports(report, tmp_path, ["html"])
