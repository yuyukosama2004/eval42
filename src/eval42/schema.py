"""Load and apply the bundled public JSON Schemas."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from eval42.errors import ConfigError, DatasetError, ReportError


def load_schema(name: str) -> dict[str, Any]:
    resource = files("eval42._schemas.v1").joinpath(f"{name}.schema.json")
    if resource.is_file():
        return cast(dict[str, Any], json.loads(resource.read_text(encoding="utf-8")))
    source_tree = Path(__file__).resolve().parents[2] / "schemas" / "v1"
    return cast(
        dict[str, Any],
        json.loads((source_tree / f"{name}.schema.json").read_text(encoding="utf-8")),
    )


def validate_instance(instance: Any, schema_name: str) -> None:
    validator = Draft202012Validator(load_schema(schema_name))
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
    if not errors:
        return
    error: ValidationError = errors[0]
    location = ".".join(str(part) for part in error.absolute_path) or "<root>"
    message = f"{schema_name} schema error at {location}: {error.message}"
    if schema_name == "config":
        raise ConfigError(message)
    if schema_name == "dataset-case":
        raise DatasetError(message)
    raise ReportError(message)
