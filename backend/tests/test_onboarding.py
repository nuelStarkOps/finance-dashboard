"""Profile, preferences and onboarding tests."""

from fastapi.testclient import TestClient


def _token(client: TestClient) -> str:
    client.post(
        "/api/v1/dev-auth/register",
        json={"email": "ada@example.com", "password": "password123", "display_name": "Ada"},
    )
    return client.post(
        "/api/v1/dev-auth/login",
        json={"email": "ada@example.com", "password": "password123"},
    ).json()["data"]["access_token"]


def _headers(client: TestClient) -> dict:
    return {"Authorization": f"Bearer {_token(client)}"}


def test_me_defaults(client: TestClient) -> None:
    resp = client.get("/api/v1/users/me", headers=_headers(client))
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "ada@example.com"


def test_default_preferences_nigerian(client: TestClient) -> None:
    resp = client.get("/api/v1/users/me/preferences", headers=_headers(client))
    data = resp.json()["data"]
    assert data["preferred_currency"] == "NGN"
    assert data["timezone"] == "Africa/Lagos"
    assert data["locale"] == "en-NG"
    assert data["onboarding_completed"] is False


def test_update_profile_and_preferences(client: TestClient) -> None:
    headers = _headers(client)
    resp = client.patch("/api/v1/users/me", headers=headers, json={"display_name": "Ada Lovelace"})
    assert resp.status_code == 200
    assert resp.json()["data"]["display_name"] == "Ada Lovelace"

    resp = client.patch(
        "/api/v1/users/me/preferences",
        headers=headers,
        json={"theme": "DARK", "preferred_currency": "USD"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["theme"] == "DARK"
    assert data["preferred_currency"] == "USD"


def test_onboarding_creates_first_account(client: TestClient) -> None:
    headers = _headers(client)
    payload = {
        "display_name": "Ada Lovelace",
        "country_code": "NG",
        "preferred_currency": "NGN",
        "timezone": "Africa/Lagos",
        "locale": "en-NG",
        "account": {
            "name": "Main Bank Account",
            "account_type": "CURRENT",
            "currency_code": "NGN",
            "opening_balance_minor": 15000000,
            "opening_date": "2026-11-01",
        },
    }
    resp = client.post("/api/v1/users/me/onboarding", headers=headers, json=payload)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["user"]["display_name"] == "Ada Lovelace"
    assert data["preferences"]["onboarding_completed"] is True
    assert data["preferences"]["preferred_currency"] == "NGN"
    assert data["account"]["name"] == "Main Bank Account"
    assert data["account"]["opening_balance_minor"] == 15000000

    # Preferences now reflect completed onboarding.
    prefs = client.get("/api/v1/users/me/preferences", headers=headers).json()["data"]
    assert prefs["onboarding_completed"] is True


def test_onboarding_rejects_invalid_currency(client: TestClient) -> None:
    headers = _headers(client)
    payload = {
        "display_name": "Ada",
        "country_code": "NG",
        "preferred_currency": "NG",
        "timezone": "Africa/Lagos",
        "locale": "en-NG",
        "account": {
            "name": "Acct",
            "account_type": "CURRENT",
            "currency_code": "NGN",
            "opening_balance_minor": 0,
            "opening_date": "2026-11-01",
        },
    }
    resp = client.post("/api/v1/users/me/onboarding", headers=headers, json=payload)
    assert resp.status_code == 422
