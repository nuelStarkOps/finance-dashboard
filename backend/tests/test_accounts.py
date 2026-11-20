"""Account service tests."""

from fastapi.testclient import TestClient

from tests.utils import account_balance, auth_headers, create_account


def test_create_and_list_account(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, name="Main Bank", balance=15000000)
    assert account["name"] == "Main Bank"
    assert account["currency_code"] == "NGN"
    accounts = client.get("/api/v1/accounts", headers=h).json()["data"]
    assert any(a["id"] == account["id"] for a in accounts)


def test_balance_equals_opening(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, balance=15000000)
    data = client.get(f"/api/v1/accounts/{account['id']}/balance", headers=h).json()["data"]
    assert data["opening_balance_minor"] == 15000000
    assert data["posted_minor"] == 0
    assert data["balance_minor"] == 15000000


def test_update_account(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, name="Old Name")
    updated = client.patch(
        f"/api/v1/accounts/{account['id']}", headers=h, json={"name": "New Name"}
    ).json()["data"]
    assert updated["name"] == "New Name"


def test_archive_account(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h)
    archived = client.post(f"/api/v1/accounts/{account['id']}/archive", headers=h).json()["data"]
    assert archived["status"] == "ARCHIVED"


def test_account_isolation_between_users(client: TestClient) -> None:
    h_a = auth_headers(client, email="a@example.com")
    account_a = create_account(client, h_a)
    h_b = auth_headers(client, email="b@example.com", name="Bob")
    resp = client.get(f"/api/v1/accounts/{account_a['id']}", headers=h_b)
    assert resp.status_code == 403
    assert account_balance(client, h_a, account_a["id"]) == 0
