"""Dashboard aggregation tests."""

from fastapi.testclient import TestClient

from tests.utils import auth_headers, category_id, create_account


def _tx(
    client: TestClient,
    h: dict,
    *,
    type_: str,
    amount: int,
    account_id: str,
    cat_id: str,
    description: str,
    on: str,
) -> dict:
    return client.post(
        "/api/v1/transactions",
        headers=h,
        json={
            "type": type_,
            "amount_minor": amount,
            "currency_code": "NGN",
            "account_id": account_id,
            "category_id": cat_id,
            "description": description,
            "transaction_date": on,
        },
    )


def _setup(client: TestClient):
    h = auth_headers(client)
    account = create_account(client, h, balance=100000)
    inc = category_id(client, h, "INCOME")
    exp = category_id(client, h, "EXPENSE")
    _tx(
        client,
        h,
        type_="INCOME",
        amount=50000,
        account_id=account["id"],
        cat_id=inc,
        description="Salary",
        on="2026-01-05",
    )
    _tx(
        client,
        h,
        type_="EXPENSE",
        amount=20000,
        account_id=account["id"],
        cat_id=exp,
        description="Groceries",
        on="2026-01-06",
    )
    return h, account, inc, exp


def test_summary(client: TestClient) -> None:
    h, account, _, _ = _setup(client)
    data = client.get("/api/v1/dashboard/summary", headers=h).json()["data"]
    assert data["currency_code"] == "NGN"
    assert data["income_minor"] == 50000
    assert data["expenses_minor"] == 20000
    assert data["net_cashflow_minor"] == 30000
    # opening 100000 + income 50000 - expense 20000
    assert data["total_balance_minor"] == 130000


def test_summary_date_range(client: TestClient) -> None:
    h, _, _, _ = _setup(client)
    data = client.get(
        "/api/v1/dashboard/summary",
        headers=h,
        params={"from": "2026-01-06", "to": "2026-01-31"},
    ).json()["data"]
    # Only the expense (Jan 6) is in range; income (Jan 5) is excluded.
    assert data["income_minor"] == 0
    assert data["expenses_minor"] == 20000


def test_cashflow_daily_buckets(client: TestClient) -> None:
    h, _, _, _ = _setup(client)
    data = client.get(
        "/api/v1/dashboard/cashflow",
        headers=h,
        params={"from": "2026-01-01", "to": "2026-01-31"},
    ).json()["data"]
    assert data == [
        {"period": "2026-01-05", "income_minor": 50000, "expenses_minor": 0},
        {"period": "2026-01-06", "income_minor": 0, "expenses_minor": 20000},
    ]


def test_cashflow_monthly_group(client: TestClient) -> None:
    h, _, _, _ = _setup(client)
    data = client.get(
        "/api/v1/dashboard/cashflow",
        headers=h,
        params={"from": "2026-01-01", "to": "2026-12-31", "group": "month"},
    ).json()["data"]
    assert data == [{"period": "2026-01", "income_minor": 50000, "expenses_minor": 20000}]


def test_spending_by_category(client: TestClient) -> None:
    h, account, _, _ = _setup(client)
    # Add a second expense category and an expense in it.
    cat2 = client.post(
        "/api/v1/categories", headers=h, json={"name": "Transport", "type": "EXPENSE"}
    ).json()["data"]
    _tx(
        client,
        h,
        type_="EXPENSE",
        amount=5000,
        account_id=account["id"],
        cat_id=cat2["id"],
        description="Fuel",
        on="2026-01-07",
    )

    data = client.get(
        "/api/v1/dashboard/spending", headers=h, params={"from": "2026-01-01"}
    ).json()["data"]
    totals = {c["name"]: c["total_minor"] for c in data}
    assert totals["Transport"] == 5000
    assert sum(totals.values()) == 25000


def test_recent_transactions(client: TestClient) -> None:
    h, _, _, _ = _setup(client)
    data = client.get(
        "/api/v1/dashboard/recent-transactions", headers=h, params={"limit": 1}
    ).json()["data"]
    assert len(data) == 1
    # Most recent is the Jan 6 expense.
    assert data[0]["type"] == "EXPENSE"


def test_account_overview(client: TestClient) -> None:
    h, account, _, _ = _setup(client)
    data = client.get("/api/v1/dashboard/account-overview", headers=h).json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == account["id"]
    assert data[0]["balance_minor"] == 130000


def test_budget_overview_empty(client: TestClient) -> None:
    h, _, _, _ = _setup(client)
    data = client.get("/api/v1/dashboard/budget-overview", headers=h).json()["data"]
    assert data == []
