from __future__ import annotations

from pathlib import Path

import pytest

from eval42.config import config_path, load_config, redact_config
from eval42.errors import ConfigError

from .conftest import ROOT


def test_load_config_and_relative_path() -> None:
    loaded = load_config(ROOT / "examples/mock-shopping/eval.yml")
    assert loaded.data["project"]["name"] == "mock-shopping"
    assert config_path(loaded, "dataset", "path").name == "dataset.jsonl"
    assert loaded.config_hash.startswith("sha256:")


def test_environment_default_and_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (ROOT / "examples/mock-shopping/eval.yml").read_text(encoding="utf-8")
    source = source.replace("https://offline.invalid", "${TARGET_URL:-http://default}")
    path = tmp_path / "eval.yml"
    path.write_text(source, encoding="utf-8")
    assert load_config(path).data["adapter"]["base_url"] == "http://default"
    path.write_text(source.replace("${TARGET_URL:-http://default}", "${MISSING_URL}"))
    monkeypatch.delenv("MISSING_URL", raising=False)
    with pytest.raises(ConfigError, match="MISSING_URL"):
        load_config(path)


def test_invalid_yaml_and_root(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.yml"
    invalid.write_text("[unterminated", encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid YAML"):
        load_config(invalid)
    scalar = tmp_path / "scalar.yml"
    scalar.write_text("hello", encoding="utf-8")
    with pytest.raises(ConfigError, match="root"):
        load_config(scalar)


def test_schema_error_and_missing_path(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.yml"
    invalid.write_text("schema_version: '1'\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="schema error"):
        load_config(invalid)
    loaded = load_config(ROOT / "examples/mock-shopping/eval.yml")
    with pytest.raises(ConfigError, match=r"missing\.path"):
        config_path(loaded, "missing", "path")


def test_redacts_headers() -> None:
    source = {"adapter": {"headers": {"Authorization": "secret"}}, "other": ["safe"]}
    redacted = redact_config(source)
    assert redacted["adapter"]["headers"]["Authorization"] == "***"
    assert source["adapter"]["headers"]["Authorization"] == "secret"


def test_secret_header_does_not_change_public_config_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (ROOT / "examples/mock-shopping/eval.yml").read_text(encoding="utf-8")
    source = source.replace(
        "  timeout_seconds: 5",
        "  timeout_seconds: 5\n  headers:\n    Authorization: Bearer ${TARGET_TOKEN}",
    )
    path = tmp_path / "eval.yml"
    path.write_text(source, encoding="utf-8")
    monkeypatch.setenv("TARGET_TOKEN", "first-secret")
    first = load_config(path)
    monkeypatch.setenv("TARGET_TOKEN", "second-secret")
    second = load_config(path)
    assert first.data["adapter"]["headers"] != second.data["adapter"]["headers"]
    assert first.config_hash == second.config_hash


def test_configured_cost_rates_require_provenance(tmp_path: Path) -> None:
    source = (ROOT / "examples/mock-shopping/eval.yml").read_text(encoding="utf-8")
    source = source.replace(
        "  - type: cost",
        "  - type: cost\n    input_cost_per_million: 2\n    output_cost_per_million: 4",
    )
    path = tmp_path / "eval.yml"
    path.write_text(source, encoding="utf-8")
    with pytest.raises(ConfigError, match="schema error"):
        load_config(path)
