"""Aggregate router for all v1 endpoints."""

from fastapi import APIRouter

from app.api.v1 import accounts, categories, dashboard, health, transactions, users
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(accounts.router)
api_router.include_router(categories.router)
api_router.include_router(transactions.router)
api_router.include_router(dashboard.router)

# Local development identity provider (register/login/recovery simulation).
if settings.dev_auth_enabled and settings.auth_provider == "dev":
    from app.api.v1 import dev_auth  # noqa: F401

    api_router.include_router(dev_auth.router)
