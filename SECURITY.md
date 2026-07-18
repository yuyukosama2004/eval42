# Security policy

## Supported versions

Eval42 is currently alpha. Security fixes are applied to the latest prerelease branch and release.

## Report a vulnerability

Use GitHub's private security advisory flow for this repository. Do not include live credentials,
customer data, production prompts, or a publicly exploitable target URL in an issue.

## Security model

- Eval42 sends requests only to the configured target and sends no telemetry.
- Config files may reference secrets through environment variables.
- Reports never serialize Adapter Header values.
- Full answers and retrieved content are excluded by default.
- HTTP responses are limited to 10 MiB.
- Config files cannot dynamically import or execute Python.
- The current release has no shell/Command Adapter.

Treat configs, datasets, target responses, retrieved pages, and model output as untrusted input.
Run live evaluations with least-privilege, read-only target credentials and a separate evaluation
environment.
