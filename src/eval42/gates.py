"""Stable quality gate evaluation and exit-code semantics."""

from __future__ import annotations

from collections.abc import Iterable

from eval42.models import GateResult, JsonObject

PASS = 0
EXECUTION_ERROR = 1
QUALITY_FAILURE = 2
UNTRUSTED = 3


def evaluate_gates(
    configs: Iterable[JsonObject],
    aggregate: dict[str, float],
    cases: Iterable[dict[str, float | None]],
    baseline: dict[str, float] | None = None,
) -> list[GateResult]:
    case_values = list(cases)
    results: list[GateResult] = []
    for config in configs:
        metric = str(config["metric"])
        severity = str(config.get("severity", "error"))
        if severity not in {"error", "warning", "info"}:
            severity = "error"
        if config.get("scope", "aggregate") == "every_case":
            observed_values = [
                value for metrics in case_values if (value := metrics.get(metric)) is not None
            ]
            observed = _worst_observed(observed_values, config)
            violation = any(_violates(value, config, None) for value in observed_values)
        else:
            observed = aggregate.get(metric)
            baseline_value = baseline.get(metric) if baseline else None
            regression_only = (
                ("max_regression" in config or "max_relative_regression" in config)
                and "min" not in config
                and "max" not in config
            )
            if regression_only and baseline_value is None:
                observed = None
            violation = observed is not None and _violates(observed, config, baseline_value)
        if observed is None:
            results.append(
                GateResult(
                    metric=metric,
                    status="not_applicable",
                    severity=severity,  # type: ignore[arg-type]
                    observed=None,
                    threshold=_threshold(config),
                    message=f"{metric} has no comparable observations",
                )
            )
            continue
        status = "pass"
        if violation:
            status = "fail" if severity == "error" else "warn"
        results.append(
            GateResult(
                metric=metric,
                status=status,  # type: ignore[arg-type]
                severity=severity,  # type: ignore[arg-type]
                observed=observed,
                threshold=_threshold(config),
                message=_message(metric, observed, config, violation),
            )
        )
    return results


def _threshold(config: JsonObject) -> JsonObject:
    return {
        key: value
        for key, value in config.items()
        if key in {"min", "max", "max_regression", "max_relative_regression", "scope"}
    }


def _worst_observed(values: list[float], config: JsonObject) -> float | None:
    if not values:
        return None
    return min(values) if "min" in config else max(values)


def _violates(value: float, config: JsonObject, baseline: float | None) -> bool:
    if "min" in config and value < float(config["min"]):
        return True
    if "max" in config and value > float(config["max"]):
        return True
    if (
        "max_regression" in config
        and baseline is not None
        and baseline - value > float(config["max_regression"])
    ):
        return True
    if "max_relative_regression" in config and baseline not in {None, 0.0}:
        assert baseline is not None
        if (baseline - value) / abs(baseline) > float(config["max_relative_regression"]):
            return True
    return False


def _message(metric: str, value: float, config: JsonObject, violation: bool) -> str:
    state = "violates" if violation else "satisfies"
    return f"{metric}={value:.6g} {state} {_threshold(config)}"


def gate_summary(
    results: Iterable[GateResult],
    *,
    untrusted: bool,
) -> tuple[str, int]:
    values = list(results)
    if untrusted:
        return "untrusted", UNTRUSTED
    if any(
        result.status == "fail"
        or (result.status == "not_applicable" and result.severity == "error")
        for result in values
    ):
        return "fail", QUALITY_FAILURE
    if any(result.status == "warn" for result in values):
        return "pass_with_warnings", PASS
    return "pass", PASS
