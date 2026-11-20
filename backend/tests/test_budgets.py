"""Budget calculation tests."""

from fastapi.testclient import TestClient

from tests.utils import auth_headers, category_id, create_account


def _expense(
    client: TestClient, h: dict, account_id: str, cat_id: str, amount: int, on: str = "2026-01-10"
) -> dict:
    return client.post(
        "/api/v1/transactions",
        headers=h,
        json={
            "type": "EXPENSE",
            "amount_minor": amount,
            "currency_code": "NGN",
            "account_id": account_id,
            "category_id": cat_id,
            "description": "Spend",
            "transaction_date": on,
        },
    )


def _create_budget(client: TestClient, h: dict, **overrides) -> dict:
    payload = {
        "name": "January",
        "currency_code": "NGN",
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
    }
    payload.update(overrides)
    return client.post("/api/v1/budgets", headers=h, json=payload)


def _setup(client: TestClient) -> tuple[dict, str, str]:
    h = auth_headers(client)
    account = create_account(client, h, balance=1000000)
    exp = category_id(client, h, "EXPENSE")
    return h, account["id"], exp


def test_create_overall_budget(client: TestClient) -> None:
    h, _, _ = _setup(client)
    resp = _create_budget(client, h, total_limit_minor=100000)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "January"
    assert data["total_limit_minor"] == 100000


def test_create_budget_invalid_dates(client: TestClient) -> None:
    h, _, _ = _setup(client)
    resp = _create_budget(client, h, start_date="2026-02-01", end_date="2026-01-01")
    assert resp.status_code == 422


def test_budget_duplicate_categories_rejected(client: TestClient) -> None:
    h, _, exp = _setup(client)
    resp = _create_budget(
        client,
        h,
        items=[
            {"category_id": exp, "limit_minor": 10000},
            {"category_id": exp, "limit_minor": 20000},
        ],
    )
    assert resp.status_code == 422


def test_overall_budget_usage_and_warnings(client: TestClient) -> None:
    h, account, exp = _setup(client)
    _create_budget(client, h, total_limit_minor=100000)

    _expense(client, h, account, exp, 50000)
    perf = client.get("/api/v1/budgets", headers=h).json()["data"][0]
    assert perf["id"]

    detail = client.get(f"/api/v1/budgets/{perf['id']}/performance", headers=h).json()["data"]
    assert detail["total_spent_minor"] == 50000
    assert detail["total_usage_percent"] == 50.0
    assert detail["status"] == "ok"

    _expense(client, h, account, exp, 40000)
    detail = client.get(f"/api/v1/budgets/{perf['id']}/performance", headers=h).json()["data"]
    assert detail["total_spent_minor"] == 90000
    assert detail["total_usage_percent"] == 90.0
    assert detail["status"] == "warning"

    _expense(client, h, account, exp, 20000)
    detail = client.get(f"/api/v1/budgets/{perf['id']}/performance", headers=h).json()["data"]
    assert detail["total_spent_minor"] == 110000
    assert detail["total_usage_percent"] == 110.0
    assert detail["status"] == "over"


def test_category_budget_usage(client: TestClient) -> None:
    h, account, _ = _setup(client)
    cats = client.get("/api/v1/categories", headers=h, params={"type": "EXPENSE"}).json()["data"]
    cat_a, cat_b = cats[0]["id"], cats[1]["id"]

    budget = _create_budget(
        client,
        h,
        items=[
            {"category_id": cat_a, "limit_minor": 100000},
            {"category_id": cat_b, "limit_minor": 50000},
        ],
    ).json()["data"]

    _expense(client, h, account, cat_a, 60000)
    detail = client.get(f"/api/v1/budgets/{budget['id']}/performance", headers=h).json()["data"]

    by_id = {i["category_id"]: i for i in detail["items"]}
    assert by_id[cat_a]["spent_minor"] == 60000
    assert by_id[cat_a]["usage_percent"] == 60.0
    assert by_id[cat_b]["spent_minor"] == 0
    assert by_id[cat_b]["usage_percent"] == 0.0


def test_budget_excludes_voided_expenses(client: TestClient) -> None:
    h, account, exp = _setup(client)
    budget = _create_budget(client, h, total_limit_minor=100000).json()["data"]

    tx = _expense(client, h, account, exp, 50000).json()["data"]
    client.post(f"/api/v1/transactions/{tx['id']}/void", headers=h)

    detail = client.get(f"/api/v1/budgets/{budget['id']}/performance", headers=h).json()["data"]
    assert detail["total_spent_minor"] == 0


def test_budget_isolation(client: TestClient) -> None:
    h_a = auth_headers(client, email="a@example.com")
    budget_a = _create_budget(client, h_a).json()["data"]
    h_b = auth_headers(client, email="b@example.com", name="Bob")
    resp = client.get(f"/api/v1/budgets/{budget_a['id']}", headers=h_b)
    assert resp.status_code == 403


def test_archive_budget(client: TestClient) -> None:
    h, _, _ = _setup(client)
    budget = _create_budget(client, h).json()["data"]
    archived = client.delete(f"/api/v1/budgets/{budget['id']}", headers=h).json()["data"]
    assert archived["status"] == "ARCHIVED"


def test_dashboard_budget_overview(client: TestClient) -> None:
    h, account, exp = _setup(client)
    _create_budget(client, h, total_limit_minor=100000)
    _expense(client, h, account, exp, 60000)

    data = client.get("/api/v1/dashboard/budget-overview", headers=h).json()["data"]
    assert len(data) == 1
    assert data[0]["spent_minor"] == 60000
    assert data[0]["usage_percent"] == 60.0
