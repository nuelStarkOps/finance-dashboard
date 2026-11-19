"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (register models with Base.metadata)
from app.api.v1 import dev_auth
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture(autouse=True)
def _reset_dev_auth_store():
    """Reset the in-memory dev identity store before each test."""
    with dev_auth._store_lock:
        dev_auth._dev_users.clear()
    yield


@pytest.fixture()
def client():
    """Return a TestClient wired to an in-memory SQLite database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
