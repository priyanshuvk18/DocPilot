# Citewise API (FastAPI)

Backend for Citewise. See the [repository README](../../README.md) for setup,
environment variables, and architecture.

```bash
uv sync --all-extras
uv run uvicorn app.main:app --reload --port 8000   # dev server
uv run arq app.workers.settings.WorkerSettings      # background worker
uv run pytest -m unit                               # tests
uv run ruff check . && uv run mypy app              # lint + types
```
