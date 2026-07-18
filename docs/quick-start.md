# Quick Start

This walkthrough starts from a clean checkout and ends with a machine-readable report, a reviewed
baseline, and a CI-friendly exit code. It uses no network target and no secret.

## 1. Install

```bash
git clone https://github.com/yuyukosama2004/eval42.git
cd eval42
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source .venv/bin/activate
```

Install and confirm the executable:

```bash
python -m pip install -e .
eval42 version
```

## 2. Validate and run

```bash
eval42 validate examples/mock-shopping/eval.yml
eval42 run examples/mock-shopping/eval.yml
```

Expected terminal result:

```text
PASS: 3/3 cases completed
```

Inspect:

- `examples/mock-shopping/reports/report.json` for CI or another program;
- `examples/mock-shopping/reports/report.md` for a PR artifact or human review.

The example uses `adapter.type: http`, but `fixture_path` intercepts transport with reviewed JSON.
The request mapper, response mapper, normalization, metrics, gates, and reporters are the same code
used for a real endpoint.

## 3. Create and compare a baseline

```bash
eval42 baseline create examples/mock-shopping/eval.yml \
  --output examples/mock-shopping/baseline.json

eval42 baseline compare \
  examples/mock-shopping/reports/report.json \
  examples/mock-shopping/baseline.json
```

Eval42 never overwrites a baseline automatically. Review and commit a new baseline through the
same process used for a code change.

## 4. Connect a real endpoint

Copy the nearest example config, remove `fixture_path`, set `base_url` and `endpoint`, then define
the smallest possible mappings:

```yaml
adapter:
  type: http
  base_url: ${TARGET_BASE_URL:-http://localhost:8080}
  endpoint: /evaluate
  request:
    json:
      query: $.input.query
  response_mapping:
    retrieved_items: $.retrieved_products
    recommended_ids: $.recommended_ids
    answer: $.answer
    usage: $.usage
```

Use `${NAME}` for a required environment variable and `${NAME:-default}` for a safe default.
Authorization values belong in environment-backed headers. They are not persisted in reports.

## 5. Call from an agent

Codex or Claude Code can invoke Eval42 exactly as CI does:

```bash
eval42 run path/to/eval.yml
```

The agent should interpret exit code `2` as a verified quality regression and exit code `3` as an
infrastructure or completeness problem. It should read `report.json` for details instead of
guessing from console prose.
