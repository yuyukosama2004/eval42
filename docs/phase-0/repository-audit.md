# Phase 0 Repository Audit

Audit date: 2026-07-16

## Revisions

| Repository | Revision | Version | CI evidence |
|---|---|---|---|
| Eval42 | `02f560a84c9c3701b1fe8db655769df54c7cf3c9` | `plan-v1.1.0` | Documentation workflow passed |
| PhoneMall | `2f0ecb46cffc2f16e1d63ae26be49d6c89f94320` | `v0.8.0-alpha.2-1-g2f0ecb4` | GitHub Actions run `29491590135` passed |
| GroundedSeek | `bfb0be00b400a242bb9f9ba1202e7fa6cefc2bc5` | `v1.1.0` | GitHub Actions run `29491382442` passed |

PhoneMall and GroundedSeek changes after the v1.1 plan review were documentation-only. The
functional assumptions in the plan remain valid.

## PhoneMall findings

- Production entry point: authenticated SSE `GET /api/order/ai/chat`.
- Retrieval is private `AiServiceImpl.ragSearch`, returning products without scores or ranks.
- The production path reads up to ten user conversation records and persists new messages.
- Model, prompt, temperature, output limit, budget, and blocked keywords are merchant settings.
- Retrieval first selects Top-10 and then filters by current product, SKU, and stock state.
- Missing embeddings or query embedding failures fall back to all cached products.
- Usage records total duration and character-derived token estimates, not supplier token usage.
- Product snapshot source for Phase 0:
  `sql/mock_data.sql`, SHA-256
  `580e00589b5e018f79cb5da03b24f9bf6b7482ad68c7aebee4f7a992eb37c196`.

Required Phase 1 boundary:

1. Extract one retrieval service shared by chat and evaluation.
2. Return raw retrieval and eligible candidates separately.
3. Preserve score, rank, retrieval mode, and index readiness.
4. Add a merchant-only, disabled-by-default, side-effect-free evaluation endpoint.

## GroundedSeek findings

- Existing asynchronous API exposes Run creation, status, result, cancellation, and events.
- Research Artifact v1 already contains sources, evidence, citations, hashes, warnings, and
  execution summary.
- `verification_status=supported` represents citation-label validity and warning state, not
  semantic entailment.
- Existing evaluation dataset:
  `backend/tests/eval/questions.jsonl`, 50 records, SHA-256
  `72ca3d29d4399a8beaab6e90be748ff9d254d5a18957aa122c75be67919c1d39`.
- Existing evaluation script only requires completion and at least one source.

Required Phase 3 boundary:

1. Reuse the existing Run and Artifact API without modifying GroundedSeek Core.
2. Separate input `allowed_domains` from scoring-only `accepted_domains`.
3. Select at least 15 existing cases for a deterministic Gold Set.
4. Freeze search results, page content, and model output for PR evaluation.

## Scope decision

- Eval42 v0.1 supports HTTP targets only.
- Command Adapter remains deferred until a real non-HTTP target requires it.
- Phase 0 defines contracts; it does not implement metrics or target adapters.
