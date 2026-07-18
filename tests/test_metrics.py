from __future__ import annotations

import pytest

from eval42.errors import ConfigError
from eval42.metrics import MetricRegistry, aggregate_metrics, default_registry
from eval42.models import CaseResult, EvalCase


def test_shopping_metrics(eval_case: EvalCase, case_result: CaseResult) -> None:
    registry = default_registry()
    values = registry.evaluate(
        [
            {"type": "recall_at_k", "k": 2},
            {"type": "mrr"},
            {"type": "forbidden_item_rate"},
            {"type": "constraint_pass_rate"},
            {"type": "fact_accuracy"},
            {"type": "claim_coverage"},
            {"type": "nonexistent_recommendation_count"},
            {"type": "unexpected_empty_result"},
            {"type": "latency"},
            {"type": "cost"},
        ],
        eval_case,
        case_result,
    )
    assert values["recall_at_2"] == 1
    assert values["mrr"] == 1
    assert values["constraint_pass_rate"] == 1
    assert values["fact_accuracy"] == 1
    assert values["claim_coverage"] == 1
    assert values["estimated_cost"] == 0.1


def test_research_metrics(eval_case: EvalCase, case_result: CaseResult) -> None:
    expected = {
        "accepted_domains": ["example.gov"],
        "required_evidence_matchers": [
            {"type": "contains", "value": "4.1%"},
            {"type": "regex", "value": r"4\.6%"},
        ],
        "expected_outcome": "report_conflict",
    }
    research_case = EvalCase(
        id=eval_case.id,
        input=eval_case.input,
        expected=expected,
        tags=eval_case.tags,
        metadata=eval_case.metadata,
        case_hash=eval_case.case_hash,
    )
    case_result.retrieved_items = [
        {"id": "a", "rank": 1, "score": 1, "attributes": {}},
        {"id": "b", "rank": 2, "score": 1, "attributes": {}},
    ]
    case_result.citations = [
        {"source_id": "a", "url": "https://a.example.gov/x", "snippet": "4.1%"},
        {"source_id": "b", "url": "https://b.example.gov/x", "snippet": "4.6%"},
    ]
    case_result.answer = "The forecasts conflict."
    case_result.system["outcome"] = "report_conflict"
    values = default_registry().evaluate(
        [
            {"type": "source_quality"},
            {"type": "evidence_recall"},
            {"type": "citation_validity"},
            {"type": "expected_outcome"},
            {"type": "conflict_preservation"},
        ],
        research_case,
        case_result,
    )
    assert all(value == 1 for value in values.values())


def test_unknown_metric_and_registry(eval_case: EvalCase, case_result: CaseResult) -> None:
    registry = MetricRegistry()
    registry.register("custom", lambda _config, _case, _result: {"custom_score": 0.5})
    assert registry.evaluate([{"type": "custom"}], eval_case, case_result) == {"custom_score": 0.5}
    with pytest.raises(ConfigError, match="unknown"):
        registry.evaluate([{"type": "missing"}], eval_case, case_result)
    with pytest.raises(ValueError):
        registry.register("", lambda _config, _case, _result: {})


def test_aggregate_percentiles_and_cost() -> None:
    summary = aggregate_metrics(
        [
            {"score": 0.5, "total_latency_ms": 100, "estimated_cost": 0.1},
            {"score": 1.0, "total_latency_ms": 200, "estimated_cost": 0.2},
            {"score": None, "total_latency_ms": 300, "estimated_cost": None},
        ]
    )
    assert summary["score"] == 0.75
    assert summary["p50_total_latency_ms"] == 200
    assert summary["p95_total_latency_ms"] == pytest.approx(290)
    assert summary["total_cost"] == pytest.approx(0.3)
