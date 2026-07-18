"""Deterministic built-in metrics and a small registry for library callers."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import Any
from urllib.parse import urlparse

from eval42.errors import ConfigError
from eval42.models import CaseResult, EvalCase, JsonObject
from eval42.util import percentile

MetricFunction = Callable[[JsonObject, EvalCase, CaseResult], dict[str, float | None]]


class MetricRegistry:
    """Map metric type names to deterministic evaluators."""

    def __init__(self) -> None:
        self._metrics: dict[str, MetricFunction] = {}

    def register(self, name: str, function: MetricFunction) -> None:
        if not name:
            raise ValueError("metric name cannot be empty")
        self._metrics[name] = function

    def evaluate(
        self,
        configs: Iterable[JsonObject],
        case: EvalCase,
        result: CaseResult,
    ) -> dict[str, float | None]:
        values: dict[str, float | None] = {}
        if result.status != "completed":
            return values
        for config in configs:
            metric_type = str(config["type"])
            function = self._metrics.get(metric_type)
            if function is None:
                raise ConfigError(f"unknown metric type {metric_type!r}")
            values.update(function(config, case, result))
        return values


def default_registry() -> MetricRegistry:
    registry = MetricRegistry()
    registry.register("recall_at_k", _recall_at_k)
    registry.register("mrr", _mrr)
    registry.register("forbidden_item_rate", _forbidden_item_rate)
    registry.register("constraint_pass_rate", _constraint_pass_rate)
    registry.register("fact_accuracy", _fact_accuracy)
    registry.register("claim_coverage", _claim_coverage)
    registry.register("latency", _latency)
    registry.register("cost", _cost)
    registry.register("source_quality", _source_quality)
    registry.register("evidence_recall", _evidence_recall)
    registry.register("citation_validity", _citation_validity)
    registry.register("expected_outcome", _expected_outcome)
    registry.register("conflict_preservation", _conflict_preservation)
    registry.register("nonexistent_recommendation_count", _nonexistent_recommendations)
    registry.register("unexpected_empty_result", _unexpected_empty_result)
    return registry


def _ranked_ids(result: CaseResult) -> list[str | int]:
    items = sorted(result.retrieved_items, key=lambda item: int(item.get("rank", 0)))
    ranked: list[str | int] = []
    for item in items:
        identifier = item["id"]
        if identifier not in ranked:
            ranked.append(identifier)
    return ranked


def _recall_at_k(config: JsonObject, case: EvalCase, result: CaseResult) -> dict[str, float | None]:
    k = int(config.get("k", 5))
    relevant = set(case.expected.get("relevant_ids", []))
    value = (
        None
        if not relevant
        else len(relevant.intersection(_ranked_ids(result)[:k])) / len(relevant)
    )
    return {f"recall_at_{k}": value}


def _mrr(_config: JsonObject, case: EvalCase, result: CaseResult) -> dict[str, float | None]:
    relevant = set(case.expected.get("relevant_ids", []))
    if not relevant:
        return {"mrr": None}
    rank = next(
        (
            index
            for index, identifier in enumerate(_ranked_ids(result), start=1)
            if identifier in relevant
        ),
        None,
    )
    return {"mrr": 0.0 if rank is None else 1.0 / rank}


def _forbidden_item_rate(
    _config: JsonObject,
    case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    forbidden = set(case.expected.get("forbidden_ids", []))
    if not result.recommended_ids:
        value = 0.0 if case.expected.get("expected_empty_result", False) else None
        return {"forbidden_item_rate": value}
    constraints = case.expected.get("constraints", {})
    if not isinstance(constraints, dict):
        constraints = {}
    _validate_supported_constraints(constraints)
    items = _items_by_id(result)
    count = 0
    for identifier in result.recommended_ids:
        item = items.get(identifier)
        if identifier in forbidden or item is None:
            count += 1
            continue
        attributes = item.get("attributes", {})
        if not isinstance(attributes, dict) or not _constraints_pass(attributes, constraints):
            count += 1
    return {"forbidden_item_rate": count / len(result.recommended_ids)}


def _constraint_pass_rate(
    _config: JsonObject,
    case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    constraints = case.expected.get("constraints", {})
    if not isinstance(constraints, dict) or not constraints:
        return {"constraint_pass_rate": None}
    _validate_supported_constraints(constraints)
    items = _items_by_id(result)
    if not result.recommended_ids:
        value = 1.0 if case.expected.get("expected_empty_result", False) else None
        return {"constraint_pass_rate": value}
    if "max_items" in constraints and len(result.recommended_ids) > int(constraints["max_items"]):
        return {"constraint_pass_rate": 0.0}
    passed = 0
    for identifier in result.recommended_ids:
        item = items.get(identifier)
        if item is None:
            continue
        attributes = item.get("attributes", {})
        if isinstance(attributes, dict) and _constraints_pass(attributes, constraints):
            passed += 1
    return {"constraint_pass_rate": passed / len(result.recommended_ids)}


_SUPPORTED_CONSTRAINTS = {
    "max_price",
    "min_price",
    "excluded_brands",
    "allowed_brands",
    "must_be_sellable",
    "must_be_in_stock",
    "allowed_categories",
    "excluded_categories",
    "max_items",
}


def _validate_supported_constraints(constraints: JsonObject) -> None:
    unsupported = set(constraints).difference(_SUPPORTED_CONSTRAINTS)
    if unsupported:
        names = ", ".join(sorted(unsupported))
        raise ConfigError(f"unsupported generic constraints: {names}")


def _constraint_checks(attributes: JsonObject, constraints: JsonObject) -> list[bool]:
    _validate_supported_constraints(constraints)
    checks: list[bool] = []
    if "max_price" in constraints:
        price = _number(attributes.get("price"))
        checks.append(price is not None and price <= float(constraints["max_price"]))
    if "min_price" in constraints:
        price = _number(attributes.get("price"))
        checks.append(price is not None and price >= float(constraints["min_price"]))
    if "excluded_brands" in constraints:
        brand = attributes.get("brand")
        checks.append(brand is not None and brand not in set(constraints["excluded_brands"]))
    if "allowed_brands" in constraints:
        checks.append(attributes.get("brand") in set(constraints["allowed_brands"]))
    if constraints.get("must_be_sellable"):
        checks.append(attributes.get("sellable") is True)
    if constraints.get("must_be_in_stock"):
        in_stock = attributes.get("in_stock")
        stock = _number(attributes.get("stock"))
        checks.append(in_stock is True or (stock is not None and stock > 0))
    if "allowed_categories" in constraints:
        checks.append(attributes.get("category") in set(constraints["allowed_categories"]))
    if "excluded_categories" in constraints:
        category = attributes.get("category")
        checks.append(
            category is not None and category not in set(constraints["excluded_categories"])
        )
    return checks


def _constraints_pass(attributes: JsonObject, constraints: JsonObject) -> bool:
    checks = _constraint_checks(attributes, constraints)
    return all(checks)


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _items_by_id(result: CaseResult) -> dict[str | int, JsonObject]:
    return {
        item["id"]: item
        for item in [*result.retrieved_items, *result.eligible_items]
        if "id" in item
    }


def _claim_key(claim: JsonObject) -> str | None:
    subject = claim.get("subject_id", claim.get("subject"))
    field = claim.get("field")
    if subject is None or field is None:
        return None
    return f"{subject}.{field}"


def _fact_accuracy(
    _config: JsonObject,
    case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    facts = case.expected.get("facts", {})
    if not isinstance(facts, dict) or not facts:
        return {"fact_accuracy": None}
    verifiable = [
        claim for claim in result.claims if (key := _claim_key(claim)) is not None and key in facts
    ]
    if not verifiable:
        return {"fact_accuracy": None}
    matches = sum(facts[_claim_key(claim)] == claim.get("value") for claim in verifiable)
    return {"fact_accuracy": matches / len(verifiable)}


def _claim_coverage(
    _config: JsonObject,
    case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    facts = case.expected.get("facts", {})
    if not isinstance(facts, dict) or not facts:
        return {"claim_coverage": None}
    claim_keys = {_claim_key(claim) for claim in result.claims}
    return {"claim_coverage": sum(key in claim_keys for key in facts) / len(facts)}


def _latency(
    _config: JsonObject,
    _case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    return {
        name: float(result.usage[name])
        if isinstance(result.usage.get(name), (int, float))
        else None
        for name in (
            "total_latency_ms",
            "retrieval_latency_ms",
            "first_token_latency_ms",
        )
    }


def _cost(
    _config: JsonObject,
    _case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    value = result.usage.get("estimated_cost")
    return {"estimated_cost": float(value) if isinstance(value, (int, float)) else None}


def _source_quality(
    _config: JsonObject,
    case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    accepted = set(case.expected.get("accepted_domains", []))
    if not accepted:
        return {"accepted_source_rate": None}
    domains = [_domain(citation) for citation in result.citations]
    present = [domain for domain in domains if domain]
    value = (
        0.0
        if not present
        else sum(_accepted(domain, accepted) for domain in present) / len(present)
    )
    return {"accepted_source_rate": value}


def _domain(citation: JsonObject) -> str:
    url = citation.get("url", citation.get("source_url", ""))
    return urlparse(str(url)).hostname or ""


def _accepted(domain: str, accepted: set[str]) -> bool:
    return any(domain == item or domain.endswith(f".{item}") for item in accepted)


def _evidence_recall(
    _config: JsonObject,
    case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    matchers = case.expected.get("required_evidence_matchers", [])
    if not isinstance(matchers, list) or not matchers:
        return {"evidence_recall": None}
    haystack = " ".join([result.answer or "", *(_flatten_text(item) for item in result.citations)])
    matches = 0
    for matcher in matchers:
        if not isinstance(matcher, dict):
            continue
        value = str(matcher.get("value", ""))
        if matcher.get("type") == "regex":
            matches += re.search(value, haystack, re.IGNORECASE) is not None
        else:
            matches += value.casefold() in haystack.casefold()
    return {"evidence_recall": matches / len(matchers)}


def _flatten_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)


def _citation_validity(
    _config: JsonObject,
    case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    if not result.citations:
        required = bool(case.expected.get("required_evidence_matchers", []))
        return {"citation_validity": 0.0 if required else None}
    source_ids = {item["id"] for item in result.retrieved_items}
    checks: list[bool] = []
    for citation in result.citations:
        source_id = citation.get("source_id", citation.get("id"))
        checks.append(source_id is not None and source_id in source_ids)
    return {"citation_validity": sum(checks) / len(checks)}


def _expected_outcome(
    _config: JsonObject,
    case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    expected = case.expected.get("expected_outcome")
    if expected is None:
        return {"expected_outcome_accuracy": None}
    return {"expected_outcome_accuracy": float(result.system.get("outcome") == expected)}


def _conflict_preservation(
    _config: JsonObject,
    case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    if case.expected.get("expected_outcome") != "report_conflict":
        return {"conflict_preservation": None}
    return {"conflict_preservation": float(result.system.get("outcome") == "report_conflict")}


def _nonexistent_recommendations(
    _config: JsonObject,
    _case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    known = {item["id"] for item in [*result.retrieved_items, *result.eligible_items]}
    return {
        "nonexistent_recommendation_count": float(
            sum(identifier not in known for identifier in result.recommended_ids)
        )
    }


def _unexpected_empty_result(
    _config: JsonObject,
    case: EvalCase,
    result: CaseResult,
) -> dict[str, float | None]:
    expected_empty = bool(case.expected.get("expected_empty_result", False))
    is_empty = not result.recommended_ids
    return {"unexpected_empty_result": float(is_empty and not expected_empty)}


def aggregate_metrics(case_metrics: Iterable[dict[str, float | None]]) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    for metrics in case_metrics:
        for name, value in metrics.items():
            if value is not None:
                grouped.setdefault(name, []).append(value)
    summary = {name: sum(values) / len(values) for name, values in sorted(grouped.items())}
    for name in ("total_latency_ms", "retrieval_latency_ms", "first_token_latency_ms"):
        values = grouped.get(name, [])
        if values:
            summary[f"average_{name}"] = sum(values) / len(values)
            summary[f"p50_{name}"] = percentile(values, 0.50) or 0.0
            summary[f"p95_{name}"] = percentile(values, 0.95) or 0.0
            summary[f"max_{name}"] = max(values)
    if "estimated_cost" in grouped:
        summary["average_cost"] = sum(grouped["estimated_cost"]) / len(grouped["estimated_cost"])
        summary["total_cost"] = sum(grouped["estimated_cost"])
    return summary


def metric_applicability(
    case_metrics: Iterable[dict[str, float | None]],
) -> dict[str, JsonObject]:
    metrics = list(case_metrics)
    names = sorted({name for values in metrics for name in values})
    return {
        name: {
            "applicable_cases": sum(values.get(name) is not None for values in metrics),
            "not_applicable_cases": sum(
                name in values and values.get(name) is None for values in metrics
            ),
        }
        for name in names
    }


def case_diagnostics(case: EvalCase, result: CaseResult) -> JsonObject:
    if result.status != "completed":
        return {}
    ranked = _ranked_ids(result)
    relevant = set(case.expected.get("relevant_ids", []))
    items = _items_by_id(result)
    constraints = case.expected.get("constraints", {})
    if not isinstance(constraints, dict):
        constraints = {}
    generic_constraints = {
        key: value for key, value in constraints.items() if key in _SUPPORTED_CONSTRAINTS
    }
    forbidden = set(case.expected.get("forbidden_ids", []))
    forbidden_recommendations: list[JsonObject] = []
    for identifier in result.recommended_ids:
        reasons: list[str] = []
        item = items.get(identifier)
        if identifier in forbidden:
            reasons.append("explicitly_forbidden")
        if item is None:
            reasons.append("not_in_retrieved_or_eligible_items")
        elif generic_constraints:
            attributes = item.get("attributes", {})
            if not isinstance(attributes, dict) or not _constraints_pass(
                attributes, generic_constraints
            ):
                reasons.append("constraint_violation")
        if reasons:
            forbidden_recommendations.append({"id": identifier, "reasons": reasons})

    facts = case.expected.get("facts", {})
    claims = {
        key: claim.get("value") for claim in result.claims if (key := _claim_key(claim)) is not None
    }
    incorrect_facts = []
    missing_facts = []
    if isinstance(facts, dict):
        incorrect_facts = [
            {"key": key, "expected": expected, "observed": claims[key]}
            for key, expected in facts.items()
            if key in claims and claims[key] != expected
        ]
        missing_facts = [key for key in facts if key not in claims]
    source_ids = {item["id"] for item in result.retrieved_items}
    invalid_citations = [
        citation.get("source_id", citation.get("id"))
        for citation in result.citations
        if citation.get("source_id", citation.get("id")) not in source_ids
    ]
    return {
        "missing_relevant_ids": sorted(relevant.difference(ranked), key=str),
        "forbidden_recommendations": forbidden_recommendations,
        "incorrect_facts": incorrect_facts,
        "missing_facts": missing_facts,
        "invalid_citation_source_ids": invalid_citations,
    }
