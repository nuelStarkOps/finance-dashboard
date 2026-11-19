"""Health endpoint (liveness only; does not require a database connection)."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness probe for orchestrators and local smoke tests."""
    return {"success": True, "data": {"status": "ok"}}
