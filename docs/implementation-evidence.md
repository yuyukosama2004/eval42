# Target Implementation Evidence

Record date: 2026-07-16

This document records what has actually been implemented and verified in the target projects
after the Phase 0 contracts were frozen. It is an implementation milestone record, not a claim
that candidate labels have completed human review or that live nightly evaluation has run.

## Status summary

| Plan area | Technical status | Remaining boundary |
|---|---|---|
| Phase 0 contracts and audits | Complete | License and migration decision remains open |
| Phase 1 PhoneMall retrieval loop | Implemented and merged | 20 candidate labels require owner review |
| Phase 2 baselines and CI gates | Implemented and merged | Live baseline, deployment, and secrets are not configured |
| Phase 3 GroundedSeek integration | Implemented and merged | 15 candidate labels require owner review |
| Phase 4 Core boundary confirmation | Not started | Requires real usage history and reviewed target data |

## PhoneMall evidence

Repository:
`yuyukosama2004/rag-shopping-assistant-platform`

| Delivery | Merge commit | Evidence |
|---|---|---|
| Protected retrieval evaluation endpoint | `2e3d47cbbf5152a01b32939cebfd95f8353f44e3` | PR [#56](https://github.com/yuyukosama2004/rag-shopping-assistant-platform/pull/56) |
| Deterministic 20-case evaluation core | `269311028f55b34df49fac5b70ee6640bdb9d42d` | PR [#57](https://github.com/yuyukosama2004/rag-shopping-assistant-platform/pull/57) |
| Baselines, regression gates, budgets, artifacts, nightly configuration | `5fed019f769632c5fd4d2986ed7fce8285eb1e70` | PR [#59](https://github.com/yuyukosama2004/rag-shopping-assistant-platform/pull/59) |
| Post-merge main verification | same revision | GitHub Actions run [29498604745](https://github.com/yuyukosama2004/rag-shopping-assistant-platform/actions/runs/29498604745), 14 jobs passed |
| Implementation milestone | same revision | prerelease [v0.8.0-alpha.3](https://github.com/yuyukosama2004/rag-shopping-assistant-platform/releases/tag/v0.8.0-alpha.3) |

Verified boundaries:

- the production chat and evaluation endpoint share one retrieval service;
- evaluation is merchant-only, disabled by default, read-only, and does not consume generation
  quota or write conversation history;
- the adapter preserves raw and eligible ranked candidates plus retrieval mode, index readiness,
  and index fingerprint;
- PR evaluation uses a deterministic fixture and uploads reports;
- the fixture baseline is explicitly not presented as live quality evidence.

Open governance:

- [PhoneMall issue #58](https://github.com/yuyukosama2004/rag-shopping-assistant-platform/issues/58)
  tracks human review of the 20 candidate labels.

## GroundedSeek evidence

Repository:
`yuyukosama2004/grounded-seek`

| Delivery | Merge commit | Evidence |
|---|---|---|
| Run/Artifact adapter, 15-case candidate set, frozen fixtures, metrics, PR and nightly workflows | `ed252fa26dd344c652cc79f5a1fdd934dc39945b` | PR [#21](https://github.com/yuyukosama2004/grounded-seek/pull/21) |
| Pull-request verification | same revision | GitHub Actions runs [29499610209](https://github.com/yuyukosama2004/grounded-seek/actions/runs/29499610209) and [29499651406](https://github.com/yuyukosama2004/grounded-seek/actions/runs/29499651406), 14 checks passed |
| Post-merge main verification | same revision | GitHub Actions run [29499824989](https://github.com/yuyukosama2004/grounded-seek/actions/runs/29499824989), 7 jobs passed |
| Implementation milestone | same revision | prerelease [v1.2.0-alpha.1](https://github.com/yuyukosama2004/grounded-seek/releases/tag/v1.2.0-alpha.1) |

Verified boundaries:

- fixture and live modes call the existing asynchronous Run and Research Artifact v1 API;
- GroundedSeek Core and the existing research queue were not modified;
- PR evaluation runs the real workflow, retrieval, storage, citation construction, and URL
  safety boundary with frozen search, short authored HTML, and Ollama outputs;
- `accepted_domains`, evidence matchers, and expected outcomes never enter request input;
- Source Domain, Evidence Recall, Citation Validity, and Expected Outcome all pass on 15/15
  deterministic candidate cases;
- two security cases reach the real URL safety boundary and are blocked.

Open governance:

- [GroundedSeek issue #20](https://github.com/yuyukosama2004/grounded-seek/issues/20)
  tracks owner review before the candidate set may be called a human-approved Gold Set.

## Cross-project blockers

- [Eval42 issue #3](https://github.com/yuyukosama2004/eval42/issues/3) tracks licenses and
  authorization to migrate code between repositories.
- Neither target nightly workflow is enabled. Each requires an explicitly configured protected
  service and repository settings or secrets.
- Phase 4 must not begin by copying the project-local implementations into Eval42. It begins only
  after the target projects provide enough real usage evidence to confirm the shared boundary.

## Next evidence required

1. Owners review or correct the PhoneMall and GroundedSeek candidate labels.
2. PhoneMall uses the evaluation gate across at least two real functional iterations and records
   at least one genuine regression or improvement.
3. A reviewed live baseline is created before PhoneMall nightly is enabled.
4. GroundedSeek live nightly is enabled only against a protected service with real SearXNG,
   Readers, and Ollama.
5. License and migration authorization is recorded before common code moves into Eval42.
