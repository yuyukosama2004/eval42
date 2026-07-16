# Changelog

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
