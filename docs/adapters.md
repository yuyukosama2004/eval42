# Adapter guide

## Synchronous HTTP

The Adapter builds a JSON request from the EvalCase and normalizes selected response fields:

```yaml
adapter:
  type: http
  base_url: ${TARGET_BASE_URL}
  endpoint: /evaluate
  method: POST
  timeout_seconds: 60
  headers:
    Authorization: Bearer ${TARGET_TOKEN}
  request:
    json:
      query: $.input.query
  response_mapping:
    retrieved_items: $.retrieved_products
    eligible_items: $.eligible_products
    recommended_ids: $.recommended_ids
    answer: $.answer
    claims: $.claims
    citations: $.citations
    usage: $.usage
    system: $.versions
```

`expected` fields should never appear in the request mapping. They exist only for scoring.

## Asynchronous submit/poll/result

```yaml
adapter:
  type: http
  base_url: http://localhost:8000
  endpoint: /api/v1/runs
  async_run:
    id_path: $.run_id
    status_endpoint: /api/v1/runs/{run_id}
    status_path: $.status
    success_values: [completed]
    failure_values: [failed, cancelled]
    result_endpoint: /api/v1/runs/{run_id}/result
    poll_interval_seconds: 1
    max_wait_seconds: 300
```

Queue-full, failed, cancelled, HTTP, network, mapping, and timeout outcomes remain distinct
execution errors.

## Normalized items

Each retrieved or eligible item has:

```json
{"id": 18, "score": 0.91, "rank": 1, "attributes": {"price": 3899}}
```

The normalizer recognizes `id`, `product_id`, `source_id`, or `url` as an identifier and places
other fields under `attributes`.

## Offline fixtures

Add `fixture_path` to an otherwise normal HTTP config:

```json
{
  "responses": {
    "case-id": {"retrieved_products": [], "recommended_ids": []}
  }
}
```

No URL is opened when a fixture is configured. A fixture can represent an explicit Adapter error
with `_error: {type, message, retryable}`.

## Target templates

- `examples/phonemall/eval.yml` maps the protected read-only evaluation endpoint.
- `examples/groundedseek/eval.yml` maps the existing Run and Research Artifact APIs.

The templates are compatibility documentation. Their datasets remain target-owned until human
review and data-governance acceptance are complete.
