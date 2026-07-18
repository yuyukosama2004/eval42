# Configuration reference

Every config is YAML whose parsed form validates against
`schemas/v1/config.schema.json`.

## Required sections

- `schema_version`: currently `"1"`.
- `project`: stable name and evaluated revision.
- `dataset`: JSONL path and optional tag filters.
- `adapter`: HTTP transport and mappings.
- `execution_policy`: completion, retry, and retryable-error thresholds.
- `metrics`: built-in metric declarations.
- `gates`: aggregate or every-case quality thresholds.
- `report`: JSON/Markdown formats and privacy controls.

Optional `baseline` and `run_budget` sections enable regression gates and hard execution budgets.

## Mapping syntax

Eval42 supports root `$` and dot-separated object/list paths:

```text
$
$.input.query
$.sources.0.url
```

There are no predicates, filters, expressions, or function calls. Missing optional response paths
normalize to unavailable values. A missing request path is a configuration error.

## Execution policy

```yaml
execution_policy:
  min_completion_rate: 1.0
  retries: 1
  max_retryable_error_rate: 0.0
```

Only errors marked retryable are retried. The final error is always retained in its case report.

## Gates

Supported thresholds are `min`, `max`, `max_regression`, and
`max_relative_regression`. `scope: every_case` prevents a dangerous case from being hidden by an
average. Severity is `error`, `warning`, or `info`.

Real network latency and model cost should remain warning/info gates in alpha because machine and
provider changes affect comparability.

An error-severity gate with no applicable observations is a quality failure, not a silent pass.
Use warning/info severity for intentionally optional metrics.

## Privacy

Reports include input by default and exclude full answers and retrieved content by default.
Authorization Header values never appear in reports. Eval42 performs no telemetry or upload.
