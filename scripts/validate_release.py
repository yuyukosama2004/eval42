"""Release invariants that are cheap enough to run on every pull request."""

from __future__ import annotations

import json
import os
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eval42._version import __version__  # noqa: E402
from eval42.config import load_config  # noqa: E402
from eval42.runner import run_evaluation  # noqa: E402
from eval42.schema import load_schema  # noqa: E402

SCHEMAS = ("config", "dataset-case", "case-result", "report", "baseline")
TEXT_SUFFIXES = {".md", ".py", ".toml", ".yml", ".yaml", ".json", ".jsonl"}
PRIVATE_PATTERNS = (
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
    re.compile(r"/Users/[^/\s]+"),
    re.compile(r"/home/[^/\s]+"),
)


def validate_version() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["version"] == __version__, "pyproject and package versions differ"


def validate_license() -> None:
    document = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = document["project"]
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert project["license"] == "MIT", "project license must be MIT"
    assert project["license-files"] == ["LICENSE"], "LICENSE must be package metadata"
    assert "MIT License" in license_text
    assert "Copyright (c) 2026 yuyukosama2004" in license_text
    sdist_includes = document["tool"]["hatch"]["build"]["targets"]["sdist"]["include"]
    assert "/LICENSE" in sdist_includes, "LICENSE must be included in the sdist"


def validate_release_tag() -> None:
    if os.environ.get("GITHUB_REF_TYPE") != "tag":
        return
    expected = f"v{__version__}"
    assert os.environ.get("GITHUB_REF_NAME") == expected, (
        f"release tag must be {expected}, got {os.environ.get('GITHUB_REF_NAME')!r}"
    )


def validate_bundled_schemas() -> None:
    for name in SCHEMAS:
        public = json.loads(
            (ROOT / "schemas" / "v1" / f"{name}.schema.json").read_text(encoding="utf-8")
        )
        assert load_schema(name) == public, f"bundled {name} schema differs from public schema"


def validate_offline_examples() -> None:
    for name in ("mock-shopping", "mock-research"):
        outcome = run_evaluation(
            load_config(ROOT / "examples" / name / "eval.yml"),
            write_output=False,
        )
        assert outcome.exit_code == 0, f"{name} did not pass"


def validate_no_private_paths() -> None:
    excluded = {".git", ".venv", "reports", "build", "dist"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        if any(part in excluded or part.startswith(".venv") for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in PRIVATE_PATTERNS:
            assert not pattern.search(text), f"private local path in {path.relative_to(ROOT)}"


def validate_security_gate() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    dev_dependencies = project["optional-dependencies"]["dev"]
    assert any(dependency.startswith("pip-audit>=") for dependency in dev_dependencies), (
        "pip-audit is missing from dev dependencies"
    )
    command = "python -m pip_audit --skip-editable --progress-spinner off"
    for name in ("ci.yml", "release.yml"):
        workflow = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert command in workflow, f"dependency audit is missing from {name}"


def validate_trusted_publishing_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    assert workflow.count("id-token: write") == 2
    assert "environment: testpypi" in workflow
    assert "environment: pypi" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "repository-url: https://test.pypi.org/legacy/" in workflow
    assert "gh release download" in workflow
    assert "secrets." not in workflow, "package publication must not use long-lived secrets"


def main() -> None:
    validate_version()
    validate_license()
    validate_release_tag()
    validate_bundled_schemas()
    validate_offline_examples()
    validate_no_private_paths()
    validate_security_gate()
    validate_trusted_publishing_workflow()
    print("release invariants passed")


if __name__ == "__main__":
    main()
