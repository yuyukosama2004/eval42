# Eval42

Eval42 is a lightweight, CI-first evaluation harness for verifiable AI applications.

The repository contains the reviewed development specification and the first versioned external
data contracts. The implementation will be stabilized only after validation against two real
projects:

- [PhoneMall](https://github.com/yuyukosama2004/rag-shopping-assistant-platform)
- [GroundedSeek](https://github.com/yuyukosama2004/grounded-seek)

## Current status

- Development plan: [v1.1](eval42-development-plan.md)
- Implementation status: Phase 0 complete; target Phase 1–3 technical validation merged
- First target: prove whether a real PhoneMall change improves or regresses retrieval quality
- Second target: upgrade GroundedSeek's existing evaluation data into a deterministic Gold Set
- Phase 0 acceptance record: [docs/phase-0/acceptance.md](docs/phase-0/acceptance.md)
- Target implementation evidence: [docs/implementation-evidence.md](docs/implementation-evidence.md)
- Versioned schemas: [schemas/README.md](schemas/README.md)

The plan intentionally prioritizes deterministic retrieval, constraint, fact, evidence, and
citation-validity checks. LLM-as-a-judge scoring is not a v0.1 hard gate.

## Repository history

- `plan-v1.0.0`: original development plan
- `plan-v1.1.0`: plan revised against the current PhoneMall and GroundedSeek repositories

## Validate the plan and contracts

```bash
python -m pip install "jsonschema>=4.23,<5"
python scripts/validate_plan.py
python scripts/validate_phase0.py
```

The validators check the development plan, source-repository audit, JSON schemas, executable
examples, status invariants, and truthful Phase 0 governance markers.
