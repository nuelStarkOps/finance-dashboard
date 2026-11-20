"""Report aggregation tests."""

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
    account = create_account(client, h, balance=1000000)
    inc = category_id(client, h, "INCOME")
    exp = category_id(client, h, "EXPENSE")
    return h, account["id"], inc, exp


def test_cashflow_report(client: TestClient) -> None:
    h, account, inc, exp = _setup(client)
    _tx(
        client,
        h,
        type_="INCOME",
        amount=10000,
        account_id=account,
        cat_id=inc,
        description="Salary",
        on="2026-01-05",
    )
    _tx(
        client,
        h,
        type_="EXPENSE",
        amount=4000,
        account_id=account,
        cat_id=exp,
        description="Food",
        on="2026-01-06",
    )

    data = client.get(
        "/api/v1/reports/cashflow",
        headers=h,
        params={"from": "2026-01-01", "to": "2026-01-31"},
    ).json()["data"]
    assert data == [
        {"period": "2026-01", "income_minor": 10000, "expenses_minor": 4000, "net_minor": 6000}
    ]


def test_spending_report_percent(client: TestClient) -> None:
    h, account, _, exp = _setup(client)
    cats = client.get("/api/v1/categories", headers=h, params={"type": "EXPENSE"}).json()["data"]
    _tx(
        client,
        h,
        type_="EXPENSE",
        amount=3000,
        account_id=account,
        cat_id=cats[0]["id"],
        description="A",
        on="2026-01-05",
    )
    _tx(
        client,
        h,
        type_="EXPENSE",
        amount=1000,
        account_id=account,
        cat_id=cats[1]["id"],
        description="B",
        on="2026-01-06",
    )

    data = client.get("/api/v1/reports/spending", headers=h, params={"from": "2026-01-01"}).json()[
        "data"
    ]
    total = sum(c["total_minor"] for c in data)
    assert total == 4000
    assert data[0]["total_minor"] == 3000
    assert data[0]["percent"] == 75.0


def test_savings_rate(client: TestClient) -> None:
    h, account, inc, exp = _setup(client)
    _tx(
        client,
        h,
        type_="INCOME",
        amount=10000,
        account_id=account,
        cat_id=inc,
        description="Salary",
        on="2026-01-05",
    )
    _tx(
        client,
        h,
        type_="EXPENSE",
        amount=4000,
        account_id=account,
        cat_id=exp,
        description="Food",
        on="2026-01-06",
    )

    data = client.get(
        "/api/v1/reports/savings-rate", headers=h, params={"from": "2026-01-01"}
    ).json()["data"]
    assert data["income_minor"] == 10000
    assert data["expenses_minor"] == 4000
    assert data["savings_rate_percent"] == 60.0


def test_savings_rate_null_when_no_income(client: TestClient) -> None:
    h, account, _, exp = _setup(client)
    _tx(
        client,
        h,
        type_="EXPENSE",
        amount=4000,
        account_id=account,
        cat_id=exp,
        description="Food",
        on="2026-01-06",
    )

    data = client.get(
        "/api/v1/reports/savings-rate", headers=h, params={"from": "2026-01-01"}
    ).json()["data"]
    assert data["income_minor"] == 0
    assert data["savings_rate_percent"] is None


def test_monthly_comparison(client: TestClient) -> None:
    h, account, inc, exp = _setup(client)
    _tx(
        client,
        h,
        type_="INCOME",
        amount=10000,
        account_id=account,
        cat_id=inc,
        description="Salary",
        on="2026-01-05",
    )
    _tx(
        client,
        h,
        type_="EXPENSE",
        amount=2000,
        account_id=account,
        cat_id=exp,
        description="Food",
        on="2026-02-06",
    )

    data = client.get(
        "/api/v1/reports/monthly-comparison",
        headers=h,
        params={"from": "2026-01-01", "to": "2026-02-28"},
    ).json()["data"]
    assert [d["period"] for d in data] == ["2026-01", "2026-02"]


def test_insights_with_data(client: TestClient) -> None:
    h, account, inc, exp = _setup(client)
    _tx(
        client,
        h,
        type_="INCOME",
        amount=10000,
        account_id=account,
        cat_id=inc,
        description="Salary",
        on="2026-01-05",
    )
    _tx(
        client,
        h,
        type_="EXPENSE",
        amount=4000,
        account_id=account,
        cat_id=exp,
        description="Food",
        on="2026-01-06",
    )

    data = client.get("/api/v1/reports/insights", headers=h, params={"from": "2026-01-01"}).json()[
        "data"
    ]
    types = {i["type"] for i in data}
    assert "cashflow" in types
    assert "savings_rate" in types
    assert "top_category" in types


def test_insights_no_data(client: TestClient) -> None:
    h, _, _, _ = _setup(client)
    data = client.get("/api/v1/reports/insights", headers=h).json()["data"]
    assert len(data) == 1
    assert data[0]["type"] == "no_data"


def test_export_csv(client: TestClient) -> None:
    h, account, inc, exp = _setup(client)
    _tx(
        client,
        h,
        type_="INCOME",
        amount=10000,
        account_id=account,
        cat_id=inc,
        description="Salary",
        on="2026-01-05",
    )

    resp = client.post(
        "/api/v1/reports/export",
        headers=h,
        json={"from": "2026-01-01", "to": "2026-01-31", "currency": "NGN"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "Summary" in resp.text
