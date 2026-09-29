# Contributing

Set up the lightweight development environment:

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

Use `uv sync --extra apple --extra dev` when changing speech adapters. Unit tests must not download
models, open audio devices, or require Ollama. Add a focused component-test recipe to
`docs/testing.md` when behavior needs real hardware or model weights.

Keep adapters replaceable and keep permission checks in code. New tools need a precise JSON schema,
argument validation, structured results, and tests for both success and failure.
