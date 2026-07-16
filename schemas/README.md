# Eval42 schemas

`schemas/v1/` contains the Phase 0 JSON Schema contracts for Eval42's stable external data
shapes:

- dataset cases;
- project configuration;
- normalized case results;
- reports;
- baselines.

The schemas use JSON Schema Draft 2020-12. Version `1` is a contract version, not an Eval42
package version. Compatible additions may be made within v1 only where a schema explicitly
allows extensions; incompatible changes require a new versioned directory.

Configuration may later be authored as YAML, but its parsed representation must validate against
`config.schema.json`. The JSON examples under `examples/phase0/` are executable contract
fixtures, not production datasets or accepted Gold annotations.

Run the contract checks with:

```bash
python -m pip install "jsonschema>=4.23,<5"
python scripts/validate_phase0.py
```
