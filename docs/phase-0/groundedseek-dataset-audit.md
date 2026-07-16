# GroundedSeek Dataset Audit

Source revision: `bfb0be00b400a242bb9f9ba1202e7fa6cefc2bc5`

Source hash:
`sha256:72ca3d29d4399a8beaab6e90be748ff9d254d5a18957aa122c75be67919c1d39`

## Inventory

| Category | Count | PR Gold Set eligibility | Reason |
|---|---:|---|---|
| `static_web` | 20 | Candidate after snapshotting | Stable questions, but current execution reads live web pages |
| `timely` | 10 | No | Expected answers change over time; Nightly only |
| `unverifiable` | 10 | Candidate after outcome fixture design | Useful refusal cases, but current expected outcome is not enforced |
| `conflict` | 5 | Replace evidence, retain capability | Questions describe conflict-handling instead of containing frozen conflicting evidence |
| `security` | 5 | Candidate after route verification | Must prove the unsafe URL reaches the URL safety boundary |

## Gold Set selection policy

Phase 3 will select at least 15 cases:

- 8–10 `static_web` cases with frozen official-document snapshots.
- 3–4 `unverifiable` cases with deterministic insufficient-evidence outcomes.
- 2–3 `security` cases that exercise URL blocking directly.

Conflict cases require new frozen source pairs and do not enter the first Gold Set merely because
their IDs already exist.

## Required protocol conversion

Current:

```json
{
  "question": "...",
  "accepted_domains": ["docs.python.org"]
}
```

Target:

```json
{
  "input": {
    "question": "...",
    "allowed_domains": []
  },
  "expected": {
    "accepted_domains": ["docs.python.org"],
    "required_evidence_matchers": [
      {
        "type": "contains",
        "value": "parents=True"
      }
    ],
    "expected_outcome": "completed"
  }
}
```

The expected domains and evidence matchers are never sent to GroundedSeek.

## Phase 0 conclusion

The existing dataset is useful seed material but is not yet a quality gate. Dataset conversion and
fixture capture belong to Phase 3, after the HTTP Core exists.
