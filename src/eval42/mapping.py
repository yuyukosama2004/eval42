"""A deliberately small JSON path mapper used by the HTTP adapter."""

from __future__ import annotations

from typing import Any

from eval42.errors import ConfigError


def get_path(value: Any, expression: str) -> Any:
    if expression == "$":
        return value
    if not expression.startswith("$."):
        raise ConfigError(f"mapping path must start with '$.': {expression!r}")
    current = value
    for part in expression[2:].split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if index < len(current):
                current = current[index]
                continue
        raise ConfigError(f"mapping path {expression!r} does not exist at {part!r}")
    return current


def apply_mapping(template: Any, source: Any) -> Any:
    if isinstance(template, str) and template.startswith("$"):
        return get_path(source, template)
    if isinstance(template, dict):
        return {key: apply_mapping(item, source) for key, item in template.items()}
    if isinstance(template, list):
        return [apply_mapping(item, source) for item in template]
    return template


def map_optional(source: Any, mapping: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, expression in mapping.items():
        try:
            result[key] = apply_mapping(expression, source)
        except ConfigError:
            result[key] = None
    return result
