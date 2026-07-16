#!/usr/bin/env python3
"""Validate the Phase 0 schemas, examples, and audit record."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "v1"
EXAMPLE_DIR = ROOT / "examples" / "phase0"

CONTRACTS = {
    "dataset-case": "dataset-case.json",
    "config": "config.json",
    "case-result": "case-result.json",
    "report": "report.json",
    "baseline": "baseline.json",
}

EXPECTED_REVISIONS = {
    "Eval42": "02f560a84c9c3701b1fe8db655769df54c7cf3c9",
    "PhoneMall": "2f0ecb46cffc2f16e1d63ae26be49d6c89f94320",
    "GroundedSeek": "bfb0be00b400a242bb9f9ba1202e7fa6cefc2bc5",
}

EXPECTED_SNAPSHOT_HASHES = {
    "PhoneMall": "580e00589b5e018f79cb5da03b24f9bf6b7482ad68c7aebee4f7a992eb37c196",
    "GroundedSeek": "72ca3d29d4399a8beaab6e90be748ff9d254d5a18957aa122c75be67919c1d39",
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_contracts() -> None:
    for contract, example_name in CONTRACTS.items():
        schema_path = SCHEMA_DIR / f"{contract}.schema.json"
        example_path = EXAMPLE_DIR / example_name
        schema = load_json(schema_path)
        example = load_json(example_path)

        Draft202012Validator.check_schema(schema)
        Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        ).validate(example)
        print(f"validated {example_path.relative_to(ROOT)}")


def assert_case_result_status_invariant() -> None:
    schema = load_json(SCHEMA_DIR / "case-result.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    completed = load_json(EXAMPLE_DIR / "case-result.json")

    invalid_completed = copy.deepcopy(completed)
    invalid_completed["error"] = {
        "type": "timeout",
        "message": "request timed out",
        "retryable": True,
    }
    expect_invalid(validator, invalid_completed, "completed result with an error")

    invalid_error = copy.deepcopy(completed)
    invalid_error["status"] = "error"
    invalid_error["error"] = None
    expect_invalid(validator, invalid_error, "error result without an error object")


def expect_invalid(
    validator: Draft202012Validator,
    instance: dict,
    description: str,
) -> None:
    try:
        validator.validate(instance)
    except ValidationError:
        return
    raise AssertionError(f"schema accepted invalid fixture: {description}")


def validate_audit_record() -> None:
    audit = (ROOT / "docs" / "phase-0" / "repository-audit.md").read_text(
        encoding="utf-8"
    )
    acceptance = (ROOT / "docs" / "phase-0" / "acceptance.md").read_text(
        encoding="utf-8"
    )

    for repository, revision in EXPECTED_REVISIONS.items():
        if revision not in audit:
            raise AssertionError(
                f"repository audit is missing {repository} revision {revision}"
            )

    for repository, digest in EXPECTED_SNAPSHOT_HASHES.items():
        if digest not in audit:
            raise AssertionError(
                f"repository audit is missing {repository} snapshot hash {digest}"
            )

    for task_number in range(1, 9):
        task_id = f"EVAL-{task_number:03d}"
        if task_id not in acceptance:
            raise AssertionError(f"acceptance record is missing {task_id}")

    required_governance_statements = (
        "pending human annotation",
        "blocked for Phase 6",
        "Phase 0 is not fully closed",
    )
    for statement in required_governance_statements:
        if statement not in acceptance:
            raise AssertionError(
                f"acceptance record is missing governance statement: {statement}"
            )

    print("validated Phase 0 repository audit and acceptance record")


def main() -> None:
    validate_contracts()
    assert_case_result_status_invariant()
    validate_audit_record()
    print("Phase 0 validation passed")


if __name__ == "__main__":
    main()
