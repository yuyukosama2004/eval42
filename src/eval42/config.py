"""YAML configuration loading with strict environment interpolation."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

from eval42.errors import ConfigError
from eval42.schema import validate_instance
from eval42.util import resolve_path, sha256_value

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


@dataclass(frozen=True)
class LoadedConfig:
    path: Path
    base_dir: Path
    data: dict[str, Any]
    config_hash: str


def _expand_string(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name, default = match.group(1), match.group(2)
        if name in os.environ:
            return os.environ[name]
        if default is not None:
            return default
        raise ConfigError(f"required environment variable {name!r} is not set")

    return _ENV_PATTERN.sub(replace, value)


def _expand_environment(value: Any) -> Any:
    if isinstance(value, str):
        return _expand_string(value)
    if isinstance(value, list):
        return [_expand_environment(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand_environment(item) for key, item in value.items()}
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"cannot read config {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("config root must be an object")
    return cast(dict[str, Any], raw)


def load_config(path: str | Path) -> LoadedConfig:
    config_path = Path(path).resolve()
    expanded = _expand_environment(_load_yaml(config_path))
    validate_instance(expanded, "config")
    return LoadedConfig(
        path=config_path,
        base_dir=config_path.parent,
        data=expanded,
        config_hash=sha256_value(redact_config(expanded)),
    )


def config_path(config: LoadedConfig, section: str, key: str) -> Path:
    value = config.data.get(section, {}).get(key)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{section}.{key} must be a non-empty path")
    return resolve_path(config.base_dir, value)


def redact_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return a report-safe copy without header values or environment secrets."""
    redacted = cast(dict[str, Any], _copy(config))
    adapter = redacted.get("adapter")
    if isinstance(adapter, dict) and isinstance(adapter.get("headers"), dict):
        adapter["headers"] = {key: "***" for key in adapter["headers"]}
    return redacted


def _copy(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy(item) for item in value]
    return value
