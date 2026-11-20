"""Shared test helpers."""

from fastapi.testclient import TestClient


def auth_headers(
    client: TestClient,
    email: str = "ada@example.com",
    password: str = "password123",
    name: str = "Ada",
) -> dict:
    client.post(
        "/api/v1/dev-auth/register",
        json={"email": email, "password": password, "display_name": name},
    )
    token = client.post(
        "/api/v1/dev-auth/login", json={"email": email, "password": password}
    ).json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_account(
    client: TestClient,
    headers: dict,
    *,
    name: str = "Main Bank",
    currency: str = "NGN",
    balance: int = 0,
    account_type: str = "CURRENT",
) -> dict:
    return client.post(
        "/api/v1/accounts",
        headers=headers,
        json={
            "name": name,
            "account_type": account_type,
            "currency_code": currency,
            "opening_balance_minor": balance,
            "opening_date": "2026-01-01",
        },
    ).json()["data"]


def category_id(client: TestClient, headers: dict, ctype: str) -> str:
    cats = client.get("/api/v1/categories", headers=headers, params={"type": ctype}).json()["data"]
    assert cats, f"No {ctype} categories available"
    return cats[0]["id"]


def account_balance(client: TestClient, headers: dict, account_id: str) -> int:
    return client.get(f"/api/v1/accounts/{account_id}/balance", headers=headers).json()["data"][
        "balance_minor"
    ]
