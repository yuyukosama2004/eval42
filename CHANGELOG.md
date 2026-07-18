# Changelog

## Unreleased

- Added the installable `eval42` alpha package and stable CLI.
- Added strict YAML configuration, JSONL loading, case hashing, and environment interpolation.
- Added a generic synchronous and submit/poll/result HTTP Adapter with offline fixture transport.
- Added deterministic shopping, fact, source, evidence, citation, conflict, latency, and cost
  metrics.
- Added baselines, regression comparison, aggregate/every-case gates, budgets, and stable exit
  codes.
- Added JSON and Markdown reporters plus fully offline shopping and research examples.
- Added PhoneMall and GroundedSeek declarative mapping templates without target runtime
  dependencies.
- Added strict typing, Ruff, multi-platform CI, package builds, and a test suite above 85%
  coverage.
- Added metric implementation fingerprints and explicit cost provenance for model, currency,
  price version, and calculation method.
- Verified the standalone alpha on Linux, Windows, macOS, and Python 3.11 through 3.14.
- Added dependency vulnerability audits to pull-request and tag-release gates, and moved the test
  suite to the patched pytest 9 line after detecting `PYSEC-2026-1845` in pytest 8.4.2.
- Added Quick Start, Adapter, configuration, architecture, compatibility, security, and
  contribution documentation.
- Recorded merged PhoneMall Phase 1–2 and GroundedSeek Phase 3 implementation evidence.
- Linked target CI runs, prereleases, and the remaining human-review and license blockers.
- Added Phase 0 repository and GroundedSeek dataset audits.
- Added the Phase 0 acceptance and license/data-governance records.
- Added JSON Schema Draft 2020-12 contracts for dataset cases, configuration, normalized case
  results, reports, and baselines.
- Added executable example fixtures and CI validation for all Phase 0 contracts.

## plan-v1.2.0 - 2026-07-18

- Recorded the owner-directed decision to build the standalone clean-room alpha before human Gold
  review is complete.
- Kept license, target review, real-usage, nightly, and stable-release acceptance gates unchanged.
- Reconciled the implementation evidence with Eval42 PR #5 without claiming target source-code
  migration or reviewed target quality.

## plan-v1.1.0 - 2026-07-16

- Aligned the plan with the current PhoneMall and GroundedSeek implementations.
- Replaced the proposed PhoneMall chat evaluation path with a protected, side-effect-free
  merchant evaluation endpoint.
- Required PhoneMall production chat and evaluation to share one retrieval service.
- Reused GroundedSeek's existing asynchronous Run and Research Artifact APIs.
- Replaced the proposed new GroundedSeek dataset with an audit and Gold Set upgrade of its
  existing 50 cases.
- Defined execution trust, zero-denominator, baseline comparability, schema versioning, privacy,
  and run-budget rules.
- Deferred Command Adapter until a real non-HTTP consumer exists.
- Reordered phases so the shared Core is stabilized only after both projects are validated.

## plan-v1.0.0 - 2026-07-16

- Added the original Eval42 development plan.
