# License and Data Governance Decision

Status: Eval42 alpha release decision complete; target-project decisions remain separate

## Repository licensing

The 2026-07-16 audit found no `LICENSE`, `COPYING`, or `NOTICE` file in Eval42, PhoneMall, or
GroundedSeek. On 2026-07-18, the owner selected MIT for Eval42 and confirmed that the
repository-authored synthetic Mock fixtures may be redistributed under the same license.

The resulting boundary is:

1. Eval42 source, schemas, documentation, and repository-authored synthetic Mock fixtures are
   published under the root `LICENSE`.
2. No PhoneMall or GroundedSeek source code was copied into Eval42; the standalone Core is a
   clean-room implementation based on public contracts and observed HTTP interfaces.
3. PhoneMall and GroundedSeek retain their own licensing decisions. Future code migration from
   either target still requires provenance and compatibility review.
4. No third-party full-page content or production customer data is included in Eval42 fixtures.

Decision evidence is recorded in
[Eval42 issue #3](https://github.com/yuyukosama2004/eval42/issues/3).

## Dataset governance

PhoneMall:

- The target-project candidate fixture is derived from repository mock data, not production
  customer data, and is not copied into the standalone Eval42 release.
- Eval42's `examples/mock-shopping` fixture is repository-authored synthetic data released under
  MIT.
- Final Gold cases must record the exact product snapshot hash.
- Names, addresses, phone numbers, emails, orders, and conversations are excluded.

GroundedSeek:

- Eval42's `examples/mock-research` fixture contains short repository-authored synthetic evidence
  released under MIT.
- Public examples should store short necessary evidence snippets, not full third-party pages.
- Frozen snapshots require source URL, fetch time, content hash, and reuse justification.
- Timely cases are not committed as stable truth.

## Retention

- PR reports: retain as CI artifacts according to repository settings.
- Accepted baselines: retain in Git history.
- Failed local runs containing answers or evidence: user-controlled and safe to delete.
- Production prompts, authorization headers, cookies, and API keys: never persist in reports.
