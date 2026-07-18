from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval42.errors import ConfigError, DatasetError
from eval42.loader import dataset_hash, load_dataset
from eval42.mapping import apply_mapping, get_path, map_optional

from .conftest import ROOT


def test_load_filter_limit_and_hash() -> None:
    path = ROOT / "examples/mock-shopping/dataset.jsonl"
    selected = load_dataset(path, include_tags=["empty"])
    assert [case.id for case in selected] == ["no-sellable-result"]
    assert len(load_dataset(path, exclude_tags=["empty"], limit=1)) == 1
    assert dataset_hash(path).startswith("sha256:")


def test_dataset_errors(tmp_path: Path) -> None:
    invalid = tmp_path / "bad.jsonl"
    invalid.write_text("{bad}\n", encoding="utf-8")
    with pytest.raises(DatasetError, match="invalid JSON"):
        load_dataset(invalid)
    case = json.loads(
        (ROOT / "examples/mock-shopping/dataset.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    duplicate = tmp_path / "duplicate.jsonl"
    duplicate.write_text(
        f"{json.dumps(case)}\n{json.dumps(case)}\n",
        encoding="utf-8",
    )
    with pytest.raises(DatasetError, match="duplicate"):
        load_dataset(duplicate)
    with pytest.raises(DatasetError, match="no cases"):
        load_dataset(ROOT / "examples/mock-shopping/dataset.jsonl", include_tags=["missing"])
    with pytest.raises(DatasetError, match="not found"):
        load_dataset(ROOT / "examples/mock-shopping/dataset.jsonl", case_ids=["missing"])
    case["id"] = "bad-regex"
    case["expected"]["required_evidence_matchers"] = [{"type": "regex", "value": "[unterminated"}]
    invalid_regex = tmp_path / "invalid-regex.jsonl"
    invalid_regex.write_text(json.dumps(case), encoding="utf-8")
    with pytest.raises(DatasetError, match="invalid evidence regex"):
        load_dataset(invalid_regex)


def test_mapping_paths_and_optional() -> None:
    source = {"input": {"query": "hello"}, "items": [{"id": 4}]}
    assert get_path(source, "$.items.0.id") == 4
    assert apply_mapping({"q": "$.input.query", "fixed": True}, source) == {
        "q": "hello",
        "fixed": True,
    }
    assert map_optional(source, {"found": "$.input.query", "missing": "$.x"}) == {
        "found": "hello",
        "missing": None,
    }
    with pytest.raises(ConfigError, match="start"):
        get_path(source, "input.query")
    with pytest.raises(ConfigError, match="does not exist"):
        get_path(source, "$.items.3")
