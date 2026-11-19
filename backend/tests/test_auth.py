"""Authentication flow tests against the local dev identity provider."""

from fastapi.testclient import TestClient

EMAIL = "ada@example.com"
PASSWORD = "password123"


def _register(client: TestClient, email: str = EMAIL, password: str = PASSWORD, name: str = "Ada"):
    return client.post(
        "/api/v1/dev-auth/register",
        json={"email": email, "password": password, "display_name": name},
    )


def _auth_headers(client: TestClient, email: str = EMAIL, password: str = PASSWORD) -> dict:
    token = client.post(
        "/api/v1/dev-auth/login", json={"email": email, "password": password}
    ).json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_returns_tokens_and_user(client: TestClient) -> None:
    resp = _register(client)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "Bearer"
    assert data["user"]["email"] == EMAIL
    assert data["user"]["display_name"] == "Ada"


def test_login_success(client: TestClient) -> None:
    _register(client)
    resp = client.post("/api/v1/dev-auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert resp.status_code == 200
    assert resp.json()["data"]["access_token"]


def test_login_wrong_password(client: TestClient) -> None:
    _register(client)
    resp = client.post(
        "/api/v1/dev-auth/login", json={"email": EMAIL, "password": "wrong-password"}
    )
    assert resp.status_code == 401
    assert resp.json()["success"] is False


def test_register_duplicate_email_conflict(client: TestClient) -> None:
    _register(client)
    resp = _register(client)
    assert resp.status_code == 409


def test_register_validation_error(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/dev-auth/register",
        json={"email": "not-an-email", "password": "short", "display_name": ""},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_protected_endpoint_requires_token(client: TestClient) -> None:
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_me_with_valid_token(client: TestClient) -> None:
    _register(client)
    resp = client.get("/api/v1/users/me", headers=_auth_headers(client))
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == EMAIL


def test_me_with_invalid_token(client: TestClient) -> None:
    resp = client.get("/api/v1/users/me", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401


def test_forgot_and_reset_password(client: TestClient) -> None:
    _register(client)
    resp = client.post("/api/v1/dev-auth/forgot-password", json={"email": EMAIL})
    assert resp.status_code == 200
    code = resp.json()["data"]["reset_code"]
    assert code

    reset = client.post(
        "/api/v1/dev-auth/reset-password",
        json={"email": EMAIL, "reset_code": code, "new_password": "new-password-123"},
    )
    assert reset.status_code == 200

    # Old password no longer works; new one does.
    assert (
        client.post(
            "/api/v1/dev-auth/login", json={"email": EMAIL, "password": PASSWORD}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/dev-auth/login",
            json={"email": EMAIL, "password": "new-password-123"},
        ).status_code
        == 200
    )


def test_refresh_token(client: TestClient) -> None:
    refresh_token = _register(client).json()["data"]["refresh_token"]
    resp = client.post("/api/v1/dev-auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["data"]["access_token"]


def test_refresh_rejects_access_token(client: TestClient) -> None:
    access_token = _register(client).json()["data"]["access_token"]
    resp = client.post("/api/v1/dev-auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
