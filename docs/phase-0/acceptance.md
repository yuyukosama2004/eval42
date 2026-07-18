# Phase 0 Acceptance Record

## EVAL-001 — PhoneMall path audit

Status: complete.

Evidence: `repository-audit.md` records the production chat, retrieval, filtering, settings,
history, persistence, and Usage paths at revision
`2f0ecb46cffc2f16e1d63ae26be49d6c89f94320`.

## EVAL-002 — Product fact snapshot

Status: format and source frozen; human fact review remains part of dataset authoring.

Source: PhoneMall `sql/mock_data.sql`.

SHA-256: `580e00589b5e018f79cb5da03b24f9bf6b7482ad68c7aebee4f7a992eb37c196`.

## EVAL-003 — First 20 reviewed shopping cases

Status: pending human annotation.

This is the only Phase 0 deliverable that cannot be truthfully completed from source code alone.
The example case defines the format but is explicitly not accepted as Gold annotation.

## EVAL-004 — Hard and soft constraints

Status: protocol complete.

Hard constraints live under `expected.constraints`; relevance preferences live in
`expected.relevant_ids`, tags, and annotation notes. Empty-result expectation is explicit.

## EVAL-005 — Evaluation endpoint security

Status: design complete; implementation belongs to Phase 1.

The endpoint is merchant-only, disabled by default, read-only, history-free, conversation-free,
and separate from user quota accounting.

## EVAL-006 — GroundedSeek dataset and Artifact audit

Status: complete.

Evidence: `groundedseek-dataset-audit.md` records all 50 cases, category decisions, leakage risk,
and Gold Set selection policy.

## EVAL-007 — License and migration authority

Status: Eval42 decision complete; target-project decisions remain separate.

The owner selected MIT for Eval42 and authorized redistribution of repository-authored synthetic
Mock fixtures under the same license. No PhoneMall or GroundedSeek source code was copied.
`license-and-data-governance.md` records the decision and remaining target boundary.

## EVAL-008 — Schema v1 drafts

Status: complete.

Drafts:

- `schemas/v1/dataset-case.schema.json`
- `schemas/v1/config.schema.json`
- `schemas/v1/case-result.schema.json`
- `schemas/v1/report.schema.json`
- `schemas/v1/baseline.schema.json`

Examples are under `examples/phase0/` and are validated in CI.

## Phase decision

Phase 1 implementation may start after this contract PR merges. Phase 0 is not fully closed until
the first 20 PhoneMall cases receive human-reviewed relevance labels. That annotation work can
proceed in parallel with the Phase 1 retrieval endpoint because the endpoint does not depend on
the final labels.
