# Architecture

Eval42 has a linear evaluation core:

```text
YAML config
  -> JSONL loader
  -> Adapter
  -> normalized CaseResult
  -> Metric registry
  -> Aggregator
  -> Baseline comparator
  -> Gate engine
  -> JSON / Markdown reporters
  -> stable exit code
```

The boundaries are intentional:

- Loader owns schema validation, filtering, uniqueness, and case hashes.
- Adapter owns target request/response translation and execution errors.
- Metrics are deterministic functions of one case and one normalized result.
- Aggregation has no target-project knowledge.
- Gates decide quality status but do not hide execution incompleteness.
- Reporters format already-decided results and do not call GitHub or a target.

`eval42.runner.run_evaluation` wires these components. Library callers may pass an Adapter instance
and a MetricRegistry. The CLI builds only the declarative HTTP Adapter.

## Trust model

A quality result is trusted only when the configured completion and retryable-error thresholds are
met. If execution is incomplete, exit code `3` takes precedence over a quality failure because the
quality conclusion is not complete.

Adapter errors become per-case records. Configuration, Schema, dataset, and startup errors remain
exceptions and map to exit code `1` in the CLI.

## Extensibility

The Python API is the extension point:

```python
from eval42.metrics import MetricRegistry

registry = MetricRegistry()
registry.register("my_metric", my_metric_function)
```

This keeps target-specific rules out of Core without making YAML an arbitrary-code execution
surface. A future plugin mechanism requires multiple real external consumers and a separate
security design.
