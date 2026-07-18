"""Versioned JSONL dataset loading."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from eval42.errors import DatasetError
from eval42.models import EvalCase
from eval42.schema import validate_instance
from eval42.util import sha256_bytes, sha256_value


def _selected(
    raw: dict[str, Any],
    include_tags: set[str],
    exclude_tags: set[str],
    case_ids: set[str],
) -> bool:
    tags = set(raw.get("tags", []))
    if include_tags and not include_tags.intersection(tags):
        return False
    if exclude_tags.intersection(tags):
        return False
    return not case_ids or raw.get("id") in case_ids


def load_dataset(
    path: str | Path,
    *,
    include_tags: Iterable[str] = (),
    exclude_tags: Iterable[str] = (),
    case_ids: Iterable[str] = (),
    limit: int | None = None,
) -> list[EvalCase]:
    dataset_path = Path(path)
    try:
        lines = dataset_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DatasetError(f"cannot read dataset {dataset_path}: {exc}") from exc

    include = set(include_tags)
    exclude = set(exclude_tags)
    requested_ids = set(case_ids)
    seen: set[str] = set()
    cases: list[EvalCase] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DatasetError(f"invalid JSON at {dataset_path}:{line_number}: {exc.msg}") from exc
        if not isinstance(raw, dict):
            raise DatasetError(f"dataset case at line {line_number} must be an object")
        try:
            validate_instance(raw, "dataset-case")
        except DatasetError as exc:
            raise DatasetError(f"{dataset_path}:{line_number}: {exc}") from exc
        _validate_regex_matchers(raw, dataset_path, line_number)
        case_id = str(raw["id"])
        if case_id in seen:
            raise DatasetError(f"duplicate case id {case_id!r} at line {line_number}")
        seen.add(case_id)
        if not _selected(raw, include, exclude, requested_ids):
            continue
        cases.append(
            EvalCase(
                id=case_id,
                input=dict(raw["input"]),
                expected=dict(raw["expected"]),
                tags=tuple(raw["tags"]),
                metadata=dict(raw["metadata"]),
                case_hash=sha256_value(raw),
            )
        )
        if limit is not None and len(cases) >= limit:
            break

    missing = requested_ids.difference(seen)
    if missing:
        raise DatasetError(f"requested case ids not found: {', '.join(sorted(missing))}")
    if not cases:
        raise DatasetError("dataset selection contains no cases")
    return cases


def dataset_hash(path: str | Path) -> str:
    try:
        return sha256_bytes(Path(path).read_bytes())
    except OSError as exc:
        raise DatasetError(f"cannot hash dataset {path}: {exc}") from exc


def _validate_regex_matchers(
    raw: dict[str, Any],
    dataset_path: Path,
    line_number: int,
) -> None:
    matchers = raw.get("expected", {}).get("required_evidence_matchers", [])
    for matcher in matchers:
        if matcher.get("type") != "regex":
            continue
        try:
            re.compile(matcher["value"])
        except re.error as exc:
            raise DatasetError(
                f"invalid evidence regex at {dataset_path}:{line_number}: {exc}"
            ) from exc
