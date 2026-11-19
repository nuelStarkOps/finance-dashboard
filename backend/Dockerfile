# syntax=docker/dockerfile:1
# Personal Finance OS — backend image (multi-stage, non-root runtime user).

FROM python:3.12-slim AS builder
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
# Build the project wheel and pull dependency wheels in one shot.
COPY pyproject.toml ./
COPY app ./app
RUN pip wheel --wheel-dir /wheels .

FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
# Create a non-root user before installing to own the install.
RUN addgroup --system app && adduser --system --ingroup app --no-create-home app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
# Migration assets (used in later phases).
COPY --chown=app:app alembic.ini ./alembic.ini
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=4).status==200 else 1)"
CMD ["./entrypoint.sh"]
