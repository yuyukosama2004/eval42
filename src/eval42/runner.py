"""End-to-end evaluation orchestration."""

from __future__ import annotations

import platform
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from eval42.adapters.base import Adapter
from eval42.adapters.http import HttpAdapter
from eval42.baseline import load_baseline
from eval42.config import LoadedConfig, config_path
from eval42.errors import AdapterError, ConfigError
from eval42.gates import evaluate_gates, gate_summary
from eval42.loader import dataset_hash, load_dataset
from eval42.metrics import (
    MetricRegistry,
    aggregate_metrics,
    case_diagnostics,
    default_registry,
    metric_applicability,
)
from eval42.models import CaseResult, EvalCase, JsonObject
from eval42.reporters import write_reports
from eval42.util import resolve_path, sha256_value


@dataclass(frozen=True)
class RunOutcome:
    report: dict[str, Any]
    exit_code: int
    report_paths: dict[str, Path]


@dataclass(frozen=True)
class RunOptions:
    case_ids: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    limit: int | None = None
    concurrency: int = 1
    apply_gates: bool = True
    require_fixture: bool = False
    output_dir: str | Path | None = None
    formats: tuple[str, ...] | None = None


def run_evaluation(
    config: LoadedConfig,
    *,
    adapter: Adapter | None = None,
    metrics: MetricRegistry | None = None,
    write_output: bool = True,
    compare_baseline: bool = True,
    options: RunOptions | None = None,
) -> RunOutcome:
    run_options = options or RunOptions()
    if run_options.concurrency < 1:
        raise ConfigError("concurrency must be at least 1")
    if run_options.limit is not None and run_options.limit < 1:
        raise ConfigError("limit must be at least 1")
    data = config.data
    dataset_config = data["dataset"]
    dataset_path = config_path(config, "dataset", "path")
    budget = data.get("run_budget", {})
    configured_limit = budget.get("max_cases")
    limit = run_options.limit
    if isinstance(configured_limit, int):
        limit = configured_limit if limit is None else min(limit, configured_limit)
    cases = load_dataset(
        dataset_path,
        include_tags=[*dataset_config.get("include_tags", []), *run_options.tags],
        exclude_tags=dataset_config.get("exclude_tags", []),
        case_ids=run_options.case_ids,
        limit=limit,
    )
    target_adapter = adapter or _build_adapter(config)
    if run_options.require_fixture and not getattr(target_adapter, "uses_fixtures", False):
        raise ConfigError("--mock requires adapter.fixture_path")
    registry = metrics or default_registry()
    started = datetime.now(UTC)
    started_clock = time.monotonic()
    case_reports: list[JsonObject] = []
    retryable_errors = 0
    total_cost = 0.0

    for offset in range(0, len(cases), run_options.concurrency):
        batch = cases[offset : offset + run_options.concurrency]
        budget_error = _budget_error(budget, started_clock, total_cost)
        if budget_error:
            results = [_error_result(case, target_adapter, config, budget_error) for case in batch]
        else:
            with ThreadPoolExecutor(max_workers=run_options.concurrency) as executor:
                results = list(
                    executor.map(
                        lambda case: _execute_with_retries(
                            target_adapter,
                            case,
                            int(data["execution_policy"]["retries"]),
                            config,
                        ),
                        batch,
                    )
                )
        for case, result in zip(batch, results, strict=True):
            if result.error and result.error.get("retryable"):
                retryable_errors += 1
            estimated_cost = result.usage.get("estimated_cost")
            if isinstance(estimated_cost, (int, float)):
                total_cost += float(estimated_cost)
            values = registry.evaluate(data["metrics"], case, result)
            case_reports.append(_case_report(case, result, values, data["report"]))

    completed = sum(case["status"] == "completed" for case in case_reports)
    completion_rate = completed / len(case_reports)
    aggregate = aggregate_metrics(case["metrics"] for case in case_reports)
    applicability = metric_applicability(
        case["metrics"] for case in case_reports if case["status"] == "completed"
    )
    baseline_metrics = (
        _baseline_metrics(config) if compare_baseline and run_options.apply_gates else None
    )
    gate_results = (
        evaluate_gates(
            data["gates"],
            aggregate,
            (case["metrics"] for case in case_reports),
            baseline_metrics,
        )
        if run_options.apply_gates
        else []
    )
    policy = data["execution_policy"]
    untrusted = completion_rate < float(policy["min_completion_rate"]) or retryable_errors / len(
        case_reports
    ) > float(policy["max_retryable_error_rate"])
    gate, exit_code = gate_summary(gate_results, untrusted=untrusted)
    completed_at = datetime.now(UTC)
    report = {
        "schema_version": "1",
        "run": {
            "project_name": data["project"]["name"],
            "revision": data["project"]["revision"],
            "dataset_hash": dataset_hash(dataset_path),
            "dataset_version": _dataset_version(cases),
            "started_at": started.isoformat(),
            "completed_at": completed_at.isoformat(),
            "config_hash": config.config_hash,
            "metric_hash": sha256_value(data["metrics"]),
            "adapter_version": target_adapter.version,
            "environment": platform.platform(),
        },
        "summary": {
            "gate": gate,
            "total_cases": len(case_reports),
            "completed_cases": completed,
            "completion_rate": completion_rate,
            "metrics": aggregate,
            "metric_applicability": applicability,
            "retryable_error_rate": retryable_errors / len(case_reports),
            "estimated_cost": total_cost if total_cost else None,
            "cost_kind": _cost_kind(case_reports),
        },
        "gates": [result.to_dict() for result in gate_results],
        "cases": case_reports,
    }
    paths: dict[str, Path] = {}
    if write_output:
        configured_output = run_options.output_dir or data["report"]["output_dir"]
        output_dir = resolve_path(config.base_dir, str(configured_output))
        formats = run_options.formats or tuple(data["report"]["formats"])
        paths = write_reports(report, output_dir, formats)
    return RunOutcome(report=report, exit_code=exit_code, report_paths=paths)


def _build_adapter(config: LoadedConfig) -> Adapter:
    adapter_config = config.data["adapter"]
    if adapter_config["type"] != "http":
        raise ConfigError(f"unsupported adapter type {adapter_config['type']!r}")
    return HttpAdapter(
        adapter_config,
        base_dir=config.base_dir,
        config_hash=config.config_hash,
        revision=config.data["project"]["revision"],
    )


def _execute_with_retries(
    adapter: Adapter,
    case: EvalCase,
    retries: int,
    config: LoadedConfig,
) -> CaseResult:
    attempt = 0
    while True:
        started = time.perf_counter()
        try:
            return adapter.execute(case)
        except AdapterError as exc:
            if exc.retryable and attempt < retries:
                attempt += 1
                continue
            elapsed_ms = (time.perf_counter() - started) * 1000
            return _error_result(case, adapter, config, exc, elapsed_ms)


def _error_result(
    case: EvalCase,
    adapter: Adapter,
    config: LoadedConfig,
    error: AdapterError,
    elapsed_ms: float = 0.0,
) -> CaseResult:
    return CaseResult(
        case_id=case.id,
        status="error",
        usage={
            "total_latency_ms": round(elapsed_ms, 3),
            "token_count_kind": "unavailable",
            "input_tokens": None,
            "output_tokens": None,
            "estimated_cost": None,
            "currency": None,
        },
        system={
            "adapter": type(adapter).__name__,
            "revision": config.data["project"]["revision"],
            "config_hash": config.config_hash,
        },
        error={
            "type": error.error_type,
            "message": str(error),
            "retryable": error.retryable,
        },
    )


def _budget_error(
    budget: JsonObject,
    started_clock: float,
    total_cost: float,
) -> AdapterError | None:
    duration = budget.get("max_duration_seconds")
    if isinstance(duration, (int, float)) and time.monotonic() - started_clock >= duration:
        return AdapterError("run duration budget exhausted", error_type="budget_exhausted")
    maximum_cost = budget.get("max_estimated_cost")
    if isinstance(maximum_cost, (int, float)) and total_cost >= maximum_cost:
        return AdapterError("estimated cost budget exhausted", error_type="budget_exhausted")
    return None


def _case_report(
    case: EvalCase,
    result: CaseResult,
    metrics: dict[str, float | None],
    report_config: JsonObject,
) -> JsonObject:
    report: JsonObject = {
        "case_id": case.id,
        "case_hash": case.case_hash,
        "status": result.status,
        "tags": list(case.tags),
        "metrics": metrics,
        "usage": result.usage,
        "system": result.system,
        "error": result.error,
        "diagnostics": case_diagnostics(case, result),
    }
    if report_config.get("include_inputs", True):
        report["input"] = case.input
    if report_config.get("include_answers", False):
        report["answer"] = result.answer
    if report_config.get("include_claims", True):
        report["claims"] = result.claims
    else:
        report["diagnostics"].pop("incorrect_facts", None)
        report["diagnostics"].pop("missing_facts", None)
    if report_config.get("include_retrieved_content", False):
        report["retrieved_items"] = result.retrieved_items
    return report


def _dataset_version(cases: list[EvalCase]) -> str:
    versions = {str(case.metadata.get("dataset_version", "unknown")) for case in cases}
    return versions.pop() if len(versions) == 1 else "mixed"


def _baseline_metrics(config: LoadedConfig) -> dict[str, float] | None:
    baseline_config = config.data.get("baseline")
    if not isinstance(baseline_config, dict):
        return None
    path = resolve_path(config.base_dir, str(baseline_config["path"]))
    baseline = load_baseline(path)
    values = baseline["summary"].get("metrics", {})
    return {key: float(value) for key, value in values.items() if isinstance(value, (int, float))}


def _cost_kind(cases: list[JsonObject]) -> str:
    kinds = {
        case.get("usage", {}).get("token_count_kind", "unavailable")
        for case in cases
        if case["status"] == "completed"
    }
    if not kinds or kinds == {"unavailable"}:
        return "unavailable"
    if kinds == {"actual"}:
        return "actual"
    return "estimated"
