# Alpha release readiness

Last audited: 2026-07-18 (Asia/Shanghai)

## Proven in this repository

| Requirement | Evidence | Status |
|---|---|---|
| Installable package and `eval42` executable | wheel `eval42-0.1.0a1-py3-none-any.whl`; clean virtual-environment install | Passed |
| JSONL loading and Schema validation | loader tests and Phase 0 contract validator | Passed |
| Sync and async HTTP Adapter | local HTTP integration tests, including polling failure | Passed |
| Offline shopping and research examples | release validator and clean-wheel smoke runs | Passed |
| Deterministic metrics | metric unit tests and both end-to-end reports | Passed |
| Baselines and dataset comparability | baseline round-trip/change tests | Passed |
| Stable gate exit behavior | quality and untrusted runner tests | Passed |
| JSON and Markdown reports | schema validation and reporter tests | Passed |
| Ruff, strict typing, coverage | Ruff, strict mypy, 28 tests, 90% total coverage | Passed locally |
| Package artifacts | sdist and wheel built with Hatch | Passed locally |
| Bundled Schema consistency | wheel inspection and release validator | Passed |
| PyPI name availability | official PyPI/TestPyPI simple endpoints returned 404 | Available when checked |

Artifact hashes from the initial local package build are build evidence only; the GitHub Release
workflow rebuilds artifacts from the tagged commit and publishes those authoritative files.

## Requires remote evidence

- Linux Python 3.11, 3.12, 3.14 jobs.
- Windows Python 3.13 job.
- macOS Python 3.13 job.
- Clean build/install job from the pull-request commit.
- Tag-triggered GitHub Release and uploaded sdist/wheel.

These are supplied by `.github/workflows/ci.yml` and `.github/workflows/release.yml`; they are not
claimed complete until the corresponding GitHub Actions runs succeed.

## External acceptance still open

- Eval42 owner selection of MIT or Apache-2.0 and addition of the corresponding `LICENSE`.
- PhoneMall expansion from 20 pending-review cases to at least 30 human-reviewed Gold cases.
- GroundedSeek maintainer acceptance of the 15 candidate Gold cases.
- Reviewed live baselines before either target enables a live/nightly gate.
- TestPyPI/PyPI credentials or Trusted Publishing configuration and an explicit public upload.

The alpha GitHub release must not be described as a stable open-source or PyPI release while these
items remain open. The standalone executable itself does not depend on the target Gold reviews,
but the full development-plan final checklist does.
