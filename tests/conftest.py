from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from eval42.models import CaseResult, EvalCase
from eval42.util import sha256_value

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def eval_case() -> EvalCase:
    raw: dict[str, Any] = {
        "schema_version": "1",
        "id": "case-1",
        "input": {"query": "phone"},
        "expected": {
            "relevant_ids": [1, 2],
            "forbidden_ids": [9],
            "constraints": {
                "max_price": 4000,
                "excluded_brands": ["Apple"],
                "must_be_sellable": True,
            },
            "facts": {"1.price": 3999},
        },
        "tags": ["smoke"],
        "metadata": {"dataset_version": "v1", "reviewed_by": "human"},
    }
    return EvalCase(
        id="case-1",
        input=raw["input"],
        expected=raw["expected"],
        tags=("smoke",),
        metadata=raw["metadata"],
        case_hash=sha256_value(raw),
    )


@pytest.fixture
def case_result() -> CaseResult:
    return CaseResult(
        case_id="case-1",
        status="completed",
        retrieved_items=[
            {
                "id": 1,
                "rank": 1,
                "score": 0.9,
                "attributes": {"price": 3999, "brand": "Xiaomi", "sellable": True},
            },
            {
                "id": 2,
                "rank": 2,
                "score": 0.8,
                "attributes": {"price": 3899, "brand": "Honor", "sellable": True},
            },
        ],
        eligible_items=[],
        recommended_ids=[1, 2],
        claims=[{"subject_id": 1, "field": "price", "value": 3999}],
        citations=[],
        usage={
            "total_latency_ms": 100,
            "retrieval_latency_ms": 20,
            "first_token_latency_ms": 50,
            "token_count_kind": "actual",
            "estimated_cost": 0.1,
        },
        system={
            "adapter": "test",
            "revision": "abc",
            "config_hash": f"sha256:{'0' * 64}",
        },
    )
