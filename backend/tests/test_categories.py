"""Category service tests."""

from fastapi.testclient import TestClient

from tests.utils import auth_headers


def test_list_default_categories(client: TestClient) -> None:
    h = auth_headers(client)
    cats = client.get("/api/v1/categories", headers=h).json()["data"]
    assert any(c["is_system"] and c["type"] == "INCOME" for c in cats)
    assert any(c["is_system"] and c["type"] == "EXPENSE" for c in cats)


def test_filter_categories_by_type(client: TestClient) -> None:
    h = auth_headers(client)
    incomes = client.get("/api/v1/categories", headers=h, params={"type": "INCOME"}).json()["data"]
    assert incomes and all(c["type"] == "INCOME" for c in incomes)


def test_create_custom_category(client: TestClient) -> None:
    h = auth_headers(client)
    cat = client.post(
        "/api/v1/categories",
        headers=h,
        json={"name": "Side Hustle", "type": "INCOME"},
    ).json()["data"]
    assert cat["name"] == "Side Hustle"
    assert cat["is_system"] is False


def test_duplicate_category_conflict(client: TestClient) -> None:
    h = auth_headers(client)
    client.post("/api/v1/categories", headers=h, json={"name": "Side Hustle", "type": "INCOME"})
    resp = client.post(
        "/api/v1/categories", headers=h, json={"name": "Side Hustle", "type": "INCOME"}
    )
    assert resp.status_code == 409


def test_archive_custom_category(client: TestClient) -> None:
    h = auth_headers(client)
    cat = client.post(
        "/api/v1/categories", headers=h, json={"name": "Old Cat", "type": "EXPENSE"}
    ).json()["data"]
    archived = client.post(f"/api/v1/categories/{cat['id']}/archive", headers=h).json()["data"]
    assert archived["status"] == "ARCHIVED"


def test_system_category_cannot_be_edited(client: TestClient) -> None:
    h = auth_headers(client)
    cats = client.get("/api/v1/categories", headers=h).json()["data"]
    system = next(c for c in cats if c["is_system"])
    resp = client.patch(f"/api/v1/categories/{system['id']}", headers=h, json={"name": "Hacked"})
    assert resp.status_code == 403


def test_system_category_cannot_be_archived(client: TestClient) -> None:
    h = auth_headers(client)
    cats = client.get("/api/v1/categories", headers=h).json()["data"]
    system = next(c for c in cats if c["is_system"])
    resp = client.post(f"/api/v1/categories/{system['id']}/archive", headers=h)
    assert resp.status_code == 403
