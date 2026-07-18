from __future__ import annotations

import copy
import threading
import time
from pathlib import Path

import pytest

from eval42.adapters.base import Adapter
from eval42.cli import main
from eval42.config import LoadedConfig, load_config
from eval42.errors import AdapterError, BaselineError, ConfigError
from eval42.gates import QUALITY_FAILURE, UNTRUSTED
from eval42.models import CaseResult, EvalCase
from eval42.runner import RunOptions, run_evaluation
from eval42.util import sha256_value

from .conftest import ROOT


class FailingAdapter(Adapter):
    def execute(self, _case: EvalCase) -> CaseResult:
        raise AdapterError("offline", error_type="network_error", retryable=True)


class ConcurrentAdapter(Adapter):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.active = 0
        self.max_active = 0

    def execute(self, case: EvalCase) -> CaseResult:
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        time.sleep(0.02)
        with self._lock:
            self.active -= 1
        return CaseResult(
            case_id=case.id,
            status="completed",
            usage={"total_latency_ms": 20, "token_count_kind": "unavailable"},
            system={
                "adapter": "concurrent-test",
                "revision": "test",
                "config_hash": f"sha256:{'0' * 64}",
            },
        )


def _changed_config(config: LoadedConfig, data: dict[str, object]) -> LoadedConfig:
    return LoadedConfig(config.path, config.base_dir, data, sha256_value(data))


def test_end_to_end_examples() -> None:
    shopping = run_evaluation(
        load_config(ROOT / "examples/mock-shopping/eval.yml"),
        write_output=False,
    )
    research = run_evaluation(
        load_config(ROOT / "examples/mock-research/eval.yml"),
        write_output=False,
    )
    assert shopping.exit_code == 0
    assert shopping.report["summary"]["gate"] == "pass"
    assert research.report["summary"]["metrics"]["conflict_preservation"] == 1


def test_quality_failure() -> None:
    loaded = load_config(ROOT / "examples/mock-shopping/eval.yml")
    data = copy.deepcopy(loaded.data)
    data["gates"] = [{"metric": "recall_at_3", "min": 1.1}]
    outcome = run_evaluation(_changed_config(loaded, data), write_output=False)
    assert outcome.exit_code == QUALITY_FAILURE
    no_gate = run_evaluation(
        _changed_config(loaded, data),
        write_output=False,
        options=RunOptions(apply_gates=False),
    )
    assert no_gate.exit_code == 0
    assert no_gate.report["gates"] == []


def test_untrusted_execution_and_retries() -> None:
    loaded = load_config(ROOT / "examples/mock-shopping/eval.yml")
    outcome = run_evaluation(loaded, adapter=FailingAdapter(), write_output=False)
    assert outcome.exit_code == UNTRUSTED
    assert outcome.report["summary"]["completed_cases"] == 0
    assert outcome.report["cases"][0]["error"]["retryable"] is True


def test_baseline_creation_can_ignore_missing_comparison(tmp_path: Path) -> None:
    loaded = load_config(ROOT / "examples/mock-shopping/eval.yml")
    data = copy.deepcopy(loaded.data)
    data["baseline"] = {"path": str(tmp_path / "not-created-yet.json")}
    configured = _changed_config(loaded, data)
    with pytest.raises(BaselineError):
        run_evaluation(configured, write_output=False)
    outcome = run_evaluation(configured, write_output=False, compare_baseline=False)
    assert outcome.exit_code == 0


def test_run_filters_and_concurrency_preserve_order() -> None:
    loaded = load_config(ROOT / "examples/mock-shopping/eval.yml")
    adapter = ConcurrentAdapter()
    outcome = run_evaluation(
        loaded,
        adapter=adapter,
        write_output=False,
        options=RunOptions(concurrency=3, apply_gates=False),
    )
    assert adapter.max_active > 1
    assert [case["case_id"] for case in outcome.report["cases"]] == [
        "camera-budget",
        "no-sellable-result",
        "prompt-injection",
    ]
    filtered = run_evaluation(
        loaded,
        write_output=False,
        options=RunOptions(tags=("empty",), limit=1),
    )
    assert [case["case_id"] for case in filtered.report["cases"]] == ["no-sellable-result"]
    with pytest.raises(ConfigError, match="concurrency"):
        run_evaluation(loaded, write_output=False, options=RunOptions(concurrency=0))
    with pytest.raises(ConfigError, match="limit"):
        run_evaluation(loaded, write_output=False, options=RunOptions(limit=0))
    with pytest.raises(ConfigError, match="fixture_path"):
        run_evaluation(
            loaded,
            adapter=adapter,
            write_output=False,
            options=RunOptions(require_fixture=True),
        )


def test_cli_commands(tmp_path: Path, capsys: object) -> None:
    config = ROOT / "examples/mock-shopping/eval.yml"
    dataset = ROOT / "examples/mock-shopping/dataset.jsonl"
    assert main(["version"]) == 0
    assert main(["validate", str(config)]) == 0
    assert main(["dataset", "validate", str(dataset)]) == 0
    output = tmp_path / "reports"
    assert (
        main(
            [
                "run",
                str(config),
                "--case",
                "camera-budget",
                "--limit",
                "1",
                "--concurrency",
                "2",
                "--no-gate",
                "--mock",
                "--output",
                str(output),
                "--format",
                "json",
                "--verbose",
            ]
        )
        == 0
    )
    assert (output / "report.json").is_file()
    assert not (output / "report.md").exists()
    baseline = tmp_path / "baseline.json"
    assert main(["baseline", "create", str(config), "--output", str(baseline)]) == 0
    report = ROOT / "examples/mock-shopping/reports/report.json"
    assert main(["baseline", "compare", str(report), str(baseline)]) == 0
    markdown = tmp_path / "report.md"
    assert main(["report", str(report), "--output", str(markdown)]) == 0
    assert markdown.read_text(encoding="utf-8").startswith("# Eval42 report")
    assert main(["validate", str(tmp_path / "missing.yml")]) == 1
