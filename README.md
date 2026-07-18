# Eval42

Eval42 is a standalone, CI-first evaluation tool for verifiable AI applications. It loads
versioned JSONL cases, calls a target through a declarative HTTP adapter, calculates deterministic
metrics, compares a reviewed baseline, applies quality gates, and writes JSON and Markdown reports.

This repository now contains an installable alpha implementation. PhoneMall and GroundedSeek are
validation consumers, not runtime dependencies.

## What it is

Eval42 is both:

- a command-line tool that humans, CI, Codex, and Claude Code can invoke;
- a Python library for applications that need to supply a custom in-process Adapter or Metric.

It is not an autonomous agent. It does not decide what to change, call an LLM judge by default,
upload data, or modify the evaluated system.

## Five-minute offline run

Python 3.11 or newer is required.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e .
eval42 run examples/mock-shopping/eval.yml
eval42 run examples/mock-research/eval.yml
```

Both examples are deterministic and make no network calls. Reports are written beside each
example under `reports/`.

## Core commands

```text
eval42 run <config>
eval42 validate <config>
eval42 dataset validate <dataset>
eval42 baseline create <config> --output <baseline.json>
eval42 baseline compare <report.json> <baseline.json>
eval42 report <report.json> [--output report.md]
eval42 version
```

`eval42 run --help` lists case/tag filters, limits, bounded concurrency, fixture-only mode,
gate suppression, output/format overrides, and verbose case output.

Stable exit codes:

| Code | Meaning |
|---:|---|
| 0 | Evaluation passed (warnings may be present) |
| 1 | Configuration, dataset, or startup error |
| 2 | Trusted run failed a quality gate |
| 3 | Partial or unreliable execution; quality conclusion is untrusted |

## Adapting a system

The built-in HTTP Adapter supports:

- `GET` and `POST`;
- request and response mapping with deliberately small `$.field.path` expressions;
- submit/poll/result APIs such as GroundedSeek;
- retryable HTTP/network errors;
- a 10 MiB response limit;
- a fixture transport for offline CI.

See [Quick Start](docs/quick-start.md), [Adapter guide](docs/adapters.md), and the
[configuration reference](docs/configuration.md).

Templates for [PhoneMall](examples/phonemall/eval.yml) and
[GroundedSeek](examples/groundedseek/eval.yml) show the complete mapping without copying either
project's implementation or data.

## Built-in deterministic metrics

- Recall@K and MRR
- forbidden-item rate, generic constraints, and nonexistent recommendations
- structured fact accuracy and claim coverage
- source-domain quality, evidence recall, and citation validity
- expected outcome and conflict preservation
- latency percentiles and explicitly typed cost/token availability

Metric functions can also be registered through the Python API. Config files never dynamically
import or execute arbitrary Python.

## Project status

- Package version: `0.1.0a1`
- Contracts: Schema v1
- License: [MIT](LICENSE)
- Local verification: Python 3.13, strict mypy, Ruff, and more than 85% test coverage
- CI target: Python 3.11–3.14 on Linux, plus Windows and macOS
- Release status: alpha; public package-index publication is not yet claimed

Eval42 source, schemas, documentation, and the repository-authored synthetic Mock fixtures are
published under the MIT License. PhoneMall and GroundedSeek source code was not copied into this
repository; their licensing and human Gold review remain separate governance concerns documented
in [license and data governance](docs/phase-0/license-and-data-governance.md).

## Design boundaries

- No telemetry, account, or hosted control plane.
- No Command Adapter in v0.1.
- No complex template language or dynamic config plugins.
- No uncalibrated LLM judge in a hard gate.
- Expected answers are never included in Adapter requests.
- A single case failure is recorded without discarding other results.

The full rationale and staged acceptance criteria remain in the
[development plan](eval42-development-plan.md). Target validation evidence is recorded in
[implementation evidence](docs/implementation-evidence.md).
