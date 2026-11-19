#!/bin/sh
# Apply pending migrations, then start the API server.
# In production, migrations are run as a controlled pre-deploy step; applying
# them idempotently here is a convenience for the local/container workflow.
set -e

alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
