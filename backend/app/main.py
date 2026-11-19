"""Application entrypoint."""

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    redoc_url="/api/v1/redoc",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    """Simple landing response; the frontend is served separately."""
    return {"service": settings.app_name, "status": "running", "docs": "/api/v1/docs"}
