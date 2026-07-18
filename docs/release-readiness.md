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
| Ruff, strict typing, coverage | Ruff, strict mypy, 39 tests, 89.73% total coverage | Passed locally and remotely |
| Dependency vulnerability audit | `pip-audit`; editable local package excluded, all resolved dependencies audited | Passed locally and enforced in CI/release |
| License and fixture redistribution | Owner-selected MIT; repository-authored synthetic fixtures included | Passed |
| Package artifacts | sdist and wheel rebuilt from tagged commit by GitHub Actions | Passed |
| Bundled Schema consistency | wheel inspection and release validator | Passed |
| Release-asset install | Downloaded wheel installed with pipx; offline shopping example passed 3/3 | Passed |
| PyPI name availability | official PyPI/TestPyPI simple endpoints returned 404 | Available when checked |
| Tokenless package-index workflow | PR [#11](https://github.com/yuyukosama2004/eval42/pull/11), GitHub Release artifact validation, stable-version gate, and separate protected environments | Implemented; account binding pending |

Authoritative [v0.1.0a1 release](https://github.com/yuyukosama2004/eval42/releases/tag/v0.1.0a1)
asset hashes:

- wheel: `sha256:136fb831dbf44272a54062436b2eef905cecbebd198d4c3a0f3275ad9a55f92d`
- sdist: `sha256:24cf1384cbf57100532f86a6f9c888ed07fbb80c44f069a23816446013ad18b5`

## Remote evidence

| Requirement | Evidence | Status |
|---|---|---|
| Linux Python 3.11, 3.12, 3.14 | [main CI run 29645320580](https://github.com/yuyukosama2004/eval42/actions/runs/29645320580) | Passed |
| Windows Python 3.13 | [main CI run 29645320580](https://github.com/yuyukosama2004/eval42/actions/runs/29645320580) | Passed |
| macOS Python 3.13 | [main CI run 29645320580](https://github.com/yuyukosama2004/eval42/actions/runs/29645320580) | Passed |
| Quality, security audit, contracts, and clean build/install | [main CI run 29645320580](https://github.com/yuyukosama2004/eval42/actions/runs/29645320580) | Passed |
| Development-plan validation | [Documentation run 29645320663](https://github.com/yuyukosama2004/eval42/actions/runs/29645320663) | Passed |
| Tag-triggered GitHub prerelease with sdist/wheel | [Release run 29644174857](https://github.com/yuyukosama2004/eval42/actions/runs/29644174857) | Passed |
| Repository-side publishing milestone | [publishing-pipeline-v1.0.0](https://github.com/yuyukosama2004/eval42/releases/tag/publishing-pipeline-v1.0.0) | Recorded; no package-index upload claimed |

## External acceptance still open

- PhoneMall expansion from 20 pending-review cases to at least 30 human-reviewed Gold cases.
- GroundedSeek maintainer acceptance of the 15 candidate Gold cases.
- Reviewed live baselines before either target enables a live/nightly gate.
- PyPI and TestPyPI account-side Trusted Publisher binding, followed by a TestPyPI upload/install;
  tracked in [issue #13](https://github.com/yuyukosama2004/eval42/issues/13).
- Stable PyPI publication remains gated on the target Gold reviews and reviewed live baselines above.

The alpha GitHub release must not be described as a stable or PyPI release while these items remain
open. The repository-side workflow intentionally accepts the alpha on TestPyPI but rejects it for
PyPI. The standalone executable itself does not depend on the target Gold reviews, but the full
development-plan final checklist does.
