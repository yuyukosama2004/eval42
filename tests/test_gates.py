from __future__ import annotations

from eval42.gates import PASS, QUALITY_FAILURE, UNTRUSTED, evaluate_gates, gate_summary


def test_aggregate_and_regression_gates() -> None:
    results = evaluate_gates(
        [
            {"metric": "quality", "min": 0.8},
            {"metric": "cost", "max": 1.0, "severity": "warning"},
            {"metric": "quality", "max_regression": 0.05},
            {"metric": "missing", "min": 1},
        ],
        {"quality": 0.7, "cost": 2.0},
        [{"quality": 0.7}],
        {"quality": 0.9},
    )
    assert [result.status for result in results] == ["fail", "warn", "fail", "not_applicable"]
    assert gate_summary(results, untrusted=False) == ("fail", QUALITY_FAILURE)
    assert gate_summary(results, untrusted=True) == ("untrusted", UNTRUSTED)


def test_every_case_and_pass_with_warning() -> None:
    results = evaluate_gates(
        [
            {"metric": "score", "min": 0.5, "scope": "every_case"},
            {"metric": "latency", "max": 10, "severity": "warning"},
        ],
        {"latency": 11},
        [{"score": 1.0}, {"score": 0.9}],
    )
    assert results[0].status == "pass"
    assert gate_summary(results, untrusted=False) == ("pass_with_warnings", PASS)


def test_regression_gate_without_baseline_is_not_applicable() -> None:
    [result] = evaluate_gates(
        [{"metric": "score", "max_regression": 0.1}],
        {"score": 0.9},
        [{"score": 0.9}],
    )
    assert result.status == "not_applicable"
