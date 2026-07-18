"""Validate distributions before an OIDC package-index publication."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from email.message import Message
from email.parser import BytesParser
from pathlib import Path
from typing import BinaryIO

from packaging.version import InvalidVersion, Version

PROJECT_NAME = "eval42"
TARGETS = ("testpypi", "pypi")


def _metadata(stream: BinaryIO) -> Message:
    return BytesParser().parse(stream)


def _wheel_metadata(path: Path) -> Message:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(names) != 1:
            raise ValueError(f"{path.name} must contain exactly one METADATA file")
        with archive.open(names[0]) as stream:
            return _metadata(stream)


def _sdist_metadata(path: Path) -> Message:
    with tarfile.open(path, "r:gz") as archive:
        members = [
            member
            for member in archive.getmembers()
            if member.isfile() and member.name.count("/") == 1 and member.name.endswith("/PKG-INFO")
        ]
        if len(members) != 1:
            raise ValueError(f"{path.name} must contain exactly one top-level PKG-INFO file")
        stream = archive.extractfile(members[0])
        if stream is None:
            raise ValueError(f"could not read metadata from {path.name}")
        with stream:
            return _metadata(stream)


def _expected_version(tag: str) -> Version:
    if not tag.startswith("v"):
        raise ValueError("release tag must start with 'v'")
    try:
        version = Version(tag[1:])
    except InvalidVersion as error:
        raise ValueError(f"invalid release tag: {tag}") from error
    if str(version) != tag[1:]:
        raise ValueError(f"release tag must use canonical version spelling: v{version}")
    return version


def _validate_metadata(metadata: Message, expected: Version, artifact: Path) -> None:
    if metadata["Name"] != PROJECT_NAME:
        raise ValueError(f"{artifact.name} project name is not {PROJECT_NAME}")
    if metadata["Version"] != str(expected):
        raise ValueError(f"{artifact.name} version does not match v{expected}")
    if metadata["License-Expression"] != "MIT":
        raise ValueError(f"{artifact.name} license expression is not MIT")


def validate_distributions(dist: Path, tag: str, target: str) -> None:
    if target not in TARGETS:
        raise ValueError(f"unsupported target: {target}")
    expected = _expected_version(tag)
    if target == "pypi" and (expected.is_prerelease or expected.is_devrelease):
        raise ValueError("PyPI publication requires a stable version")

    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("publication requires exactly one wheel and one source distribution")

    _validate_metadata(_wheel_metadata(wheels[0]), expected, wheels[0])
    _validate_metadata(_sdist_metadata(sdists[0]), expected, sdists[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--target", choices=TARGETS, required=True)
    args = parser.parse_args()
    validate_distributions(args.dist, args.tag, args.target)
    print(f"{args.tag} distributions are valid for {args.target}")


if __name__ == "__main__":
    main()
