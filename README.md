# Eval42

Eval42 is a planned lightweight, CI-first evaluation harness for verifiable AI applications.

The repository currently contains the reviewed development specification. The implementation
will be stabilized only after validation against two real projects:

- [PhoneMall](https://github.com/yuyukosama2004/rag-shopping-assistant-platform)
- [GroundedSeek](https://github.com/yuyukosama2004/grounded-seek)

## Current status

- Development plan: [v1.1](eval42-development-plan.md)
- Implementation status: pre-development
- First target: prove whether a real PhoneMall change improves or regresses retrieval quality
- Second target: upgrade GroundedSeek's existing evaluation data into a deterministic Gold Set

The plan intentionally prioritizes deterministic retrieval, constraint, fact, evidence, and
citation-validity checks. LLM-as-a-judge scoring is not a v0.1 hard gate.

## Repository history

- `plan-v1.0.0`: original development plan
- `plan-v1.1.0`: plan revised against the current PhoneMall and GroundedSeek repositories

## Validate the plan

```bash
python scripts/validate_plan.py
```

The validator checks required sections, reviewed repository revisions, stale assumptions, and
balanced fenced code blocks.
