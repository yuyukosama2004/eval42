# License and Data Governance Decision

Status: release blocker

## Repository licensing

As of 2026-07-16, Eval42, PhoneMall, and GroundedSeek do not contain a detected `LICENSE`,
`COPYING`, or `NOTICE` file.

This audit does not choose a license on the owner's behalf. Before Phase 6 code migration:

1. The owner must choose the Eval42 project license.
2. PhoneMall and GroundedSeek must state whether code may be copied into Eval42.
3. Migrated code must retain required attribution and commit provenance.
4. Eval42 must not publish copied implementation before these decisions are recorded.

Phase 0 may publish original schemas and documentation in this repository, but the absence of a
license means third-party reuse remains legally unclear.

## Dataset governance

PhoneMall:

- The initial fixture is derived from repository mock data, not production customer data.
- Final Gold cases must record the exact product snapshot hash.
- Names, addresses, phone numbers, emails, orders, and conversations are excluded.

GroundedSeek:

- Public examples should store short necessary evidence snippets, not full third-party pages.
- Frozen snapshots require source URL, fetch time, content hash, and reuse justification.
- Timely cases are not committed as stable truth.

## Retention

- PR reports: retain as CI artifacts according to repository settings.
- Accepted baselines: retain in Git history.
- Failed local runs containing answers or evidence: user-controlled and safe to delete.
- Production prompts, authorization headers, cookies, and API keys: never persist in reports.
