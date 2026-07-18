from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts.validate_publish import validate_distributions


def _metadata(version: str, license_expression: str = "MIT") -> bytes:
    return (
        "Metadata-Version: 2.4\n"
        "Name: eval42\n"
        f"Version: {version}\n"
        f"License-Expression: {license_expression}\n"
        "\n"
    ).encode()


def _write_distributions(
    dist: Path,
    version: str,
    *,
    license_expression: str = "MIT",
) -> None:
    dist.mkdir()
    metadata = _metadata(version, license_expression)
    wheel = dist / f"eval42-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(f"eval42-{version}.dist-info/METADATA", metadata)

    sdist = dist / f"eval42-{version}.tar.gz"
    with tarfile.open(sdist, "w:gz") as archive:
        info = tarfile.TarInfo(f"eval42-{version}/PKG-INFO")
        info.size = len(metadata)
        archive.addfile(info, io.BytesIO(metadata))


def test_alpha_distributions_are_allowed_on_testpypi(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_distributions(dist, "0.1.0a1")

    validate_distributions(dist, "v0.1.0a1", "testpypi")


def test_alpha_distributions_are_rejected_on_pypi(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_distributions(dist, "0.1.0a1")

    with pytest.raises(ValueError, match="requires a stable version"):
        validate_distributions(dist, "v0.1.0a1", "pypi")


def test_stable_distributions_are_allowed_on_pypi(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_distributions(dist, "0.1.0")

    validate_distributions(dist, "v0.1.0", "pypi")


def test_artifact_metadata_must_match_release(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_distributions(dist, "0.1.0", license_expression="Apache-2.0")

    with pytest.raises(ValueError, match="license expression is not MIT"):
        validate_distributions(dist, "v0.1.0", "testpypi")
