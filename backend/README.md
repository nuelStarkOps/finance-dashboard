# Personal Finance OS — backend

FastAPI modular monolith for PFOS. See the root
[README](../README.md) and [architecture docs](../docs/ARCHITECTURE.md).

## Local development

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/uvicorn app.main:app --reload --port 8000
```

- Health check: <http://localhost:8000/api/v1/health>
- API docs: <http://localhost:8000/api/v1/docs>

## Quality gates

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest
```

## Migrations

```bash
.venv/bin/alembic revision --autogenerate -m "description"
.venv/bin/alembic upgrade head
```
