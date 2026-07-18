"""Small typed models shared by the evaluation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, TypeAlias

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, Any]


@dataclass(frozen=True)
class EvalCase:
    id: str
    input: JsonObject
    expected: JsonObject
    tags: tuple[str, ...]
    metadata: JsonObject
    case_hash: str

    def as_mapping_source(self) -> JsonObject:
        return {
            "id": self.id,
            "input": self.input,
            "expected": self.expected,
            "tags": list(self.tags),
            "metadata": self.metadata,
        }


@dataclass
class CaseResult:
    case_id: str
    status: Literal["completed", "error"]
    retrieved_items: list[JsonObject] = field(default_factory=list)
    eligible_items: list[JsonObject] = field(default_factory=list)
    recommended_ids: list[str | int] = field(default_factory=list)
    answer: str | None = None
    claims: list[JsonObject] = field(default_factory=list)
    citations: list[JsonObject] = field(default_factory=list)
    usage: JsonObject = field(default_factory=dict)
    system: JsonObject = field(default_factory=dict)
    error: JsonObject | None = None

    def to_dict(self) -> JsonObject:
        return {
            "schema_version": "1",
            "case_id": self.case_id,
            "status": self.status,
            "retrieved_items": self.retrieved_items,
            "eligible_items": self.eligible_items,
            "recommended_ids": self.recommended_ids,
            "answer": self.answer,
            "claims": self.claims,
            "citations": self.citations,
            "usage": self.usage,
            "system": self.system,
            "error": self.error,
        }


@dataclass(frozen=True)
class GateResult:
    metric: str
    status: Literal["pass", "warn", "fail", "not_applicable"]
    severity: Literal["error", "warning", "info"]
    observed: float | None
    threshold: JsonObject
    message: str

    def to_dict(self) -> JsonObject:
        return {
            "metric": self.metric,
            "status": self.status,
            "severity": self.severity,
            "observed": self.observed,
            "threshold": self.threshold,
            "message": self.message,
        }
