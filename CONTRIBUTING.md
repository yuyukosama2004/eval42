# Contributing

Eval42 is in alpha and favors small changes supported by a real consumer.

## Development setup

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
mypy src
pytest --cov=eval42
python -m build
```

Run both offline examples before opening a pull request:

```bash
eval42 run examples/mock-shopping/eval.yml
eval42 run examples/mock-research/eval.yml
```

## Change rules

- Add target-specific behavior through an Adapter or Metric, not conditional imports in Core.
- Preserve stable exit codes and Schema versioning.
- Include deterministic tests for network/error paths.
- Do not commit tokens, production URLs, personal paths, customer data, full web pages, or private
  prompts.
- Do not add a plugin framework or LLM hard gate without a reviewed real-consumer requirement.
- Baselines are updated explicitly and reviewed through a pull request; CI never rewrites them.

The repository owner must finalize the project license before accepting third-party code
contributions or making a stable open-source release.
