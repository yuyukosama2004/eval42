# Compatibility decisions

This record explains what the two validation consumers changed in the generic Core.

## PhoneMall

Observed needs:

- distinguish raw retrieval from sellable candidates;
- preserve product ID, rank, score, and structured attributes;
- keep expected constraints out of the target request;
- represent actual, estimated, and unavailable token/cost data separately;
- enforce dangerous business violations per case, not only as an average.

Core decisions:

- `retrieved_items` and `eligible_items` are separate normalized fields;
- generic item attributes support price, brand, and sellability without importing PhoneMall code;
- every-case gates are part of the stable gate model;
- absent cost remains unavailable rather than zero.

## GroundedSeek

Observed needs:

- submit a Run, poll terminal state, then fetch a versioned Artifact;
- retain source/evidence/citation structures and artifact provenance;
- distinguish failed, cancelled, queue-full, and model-unavailable execution;
- evaluate frozen evidence without modifying the research queue;
- preserve a conflict outcome instead of forcing one conclusion.

Core decisions:

- HTTP Adapter supports declarative submit/poll/result flow;
- `claims`, `citations`, `system`, and `outcome` mappings are generic;
- source quality, evidence recall, citation validity, and conflict preservation are deterministic
  built-ins;
- semantic citation entailment is not claimed or used as a hard gate.

## What was not generalized

- No PhoneMall or GroundedSeek source code was copied.
- No target-specific endpoint, token, product schema, or artifact schema is imported by Core.
- No Command Adapter, arbitrary template evaluator, dynamic YAML plugin, or LLM Judge was added.

This is a clean-room implementation from the public Eval42 contracts and observed interface
requirements. Target repositories retain their own code history and licensing decisions.
