"""Notification tests (daily filing reminder)."""

from fastapi.testclient import TestClient

from tests.utils import auth_headers


def test_daily_filing_reminder_created(client: TestClient) -> None:
    h = auth_headers(client)
    data = client.get("/api/v1/notifications", headers=h).json()["data"]
    assert len(data) == 1
    assert data[0]["type"] == "daily_filing"
    assert data[0]["read_at"] is None


def test_daily_filing_reminder_idempotent(client: TestClient) -> None:
    h = auth_headers(client)
    client.get("/api/v1/notifications", headers=h)
    data = client.get("/api/v1/notifications", headers=h).json()["data"]
    assert len(data) == 1


def test_unread_count_and_mark_read(client: TestClient) -> None:
    h = auth_headers(client)
    assert client.get("/api/v1/notifications/unread-count", headers=h).json()["data"]["count"] == 1

    notification = client.get("/api/v1/notifications", headers=h).json()["data"][0]
    client.post(f"/api/v1/notifications/{notification['id']}/read", headers=h)

    assert client.get("/api/v1/notifications/unread-count", headers=h).json()["data"]["count"] == 0


def test_mark_all_read(client: TestClient) -> None:
    h = auth_headers(client)
    client.get("/api/v1/notifications", headers=h)
    client.post("/api/v1/notifications/read-all", headers=h)
    assert client.get("/api/v1/notifications/unread-count", headers=h).json()["data"]["count"] == 0
