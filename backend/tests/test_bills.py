"""Recurring bill tests (recurrence and lifecycle)."""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from tests.utils import auth_headers, category_id, create_account


def _create_bill(client: TestClient, h: dict, **overrides) -> dict:
    payload = {
        "name": "Rent",
        "amount_minor": 100000,
        "currency_code": "NGN",
        "frequency": "MONTHLY",
        "interval_value": 1,
        "next_due_date": "2026-01-31",
    }
    payload.update(overrides)
    return client.post("/api/v1/bills", headers=h, json=payload).json()["data"]


def _occurrences(client: TestClient, h: dict, bill_id: str) -> list[dict]:
    return client.get(f"/api/v1/bills/{bill_id}/occurrences", headers=h).json()["data"]


def test_create_bill_generates_occurrences(client: TestClient) -> None:
    h = auth_headers(client)
    bill = _create_bill(client, h)
    assert len(_occurrences(client, h, bill["id"])) == 12


def test_monthly_end_of_month_clamping(client: TestClient) -> None:
    h = auth_headers(client)
    bill = _create_bill(client, h, next_due_date="2026-01-31")
    dates = [o["due_date"] for o in _occurrences(client, h, bill["id"])]
    assert dates[0] == "2026-01-31"
    assert dates[1] == "2026-02-28"  # 2026 is not a leap year
    assert dates[2] == "2026-03-31"


def test_weekly_recurrence(client: TestClient) -> None:
    h = auth_headers(client)
    bill = _create_bill(client, h, frequency="WEEKLY", next_due_date="2026-01-05")
    dates = [o["due_date"] for o in _occurrences(client, h, bill["id"])]
    assert dates[0] == "2026-01-05"
    assert dates[1] == "2026-01-12"
    assert dates[2] == "2026-01-19"


def test_custom_interval_days(client: TestClient) -> None:
    h = auth_headers(client)
    bill = _create_bill(
        client, h, frequency="CUSTOM", interval_value=10, next_due_date="2026-01-01"
    )
    dates = [o["due_date"] for o in _occurrences(client, h, bill["id"])]
    assert dates[1] == "2026-01-11"


def test_occurrence_statuses(client: TestClient) -> None:
    h = auth_headers(client)
    today = date.today()
    upcoming = (today + timedelta(days=3)).isoformat()
    due = today.isoformat()
    overdue = (today - timedelta(days=3)).isoformat()

    assert (
        _occurrences(client, h, _create_bill(client, h, next_due_date=upcoming)["id"])[0]["status"]
        == "upcoming"
    )
    assert (
        _occurrences(client, h, _create_bill(client, h, next_due_date=due)["id"])[0]["status"]
        == "due"
    )
    assert (
        _occurrences(client, h, _create_bill(client, h, next_due_date=overdue)["id"])[0]["status"]
        == "overdue"
    )


def _expense(client: TestClient, h: dict, amount: int = 100000) -> dict:
    account = create_account(client, h, balance=10000000)
    exp = category_id(client, h, "EXPENSE")
    return client.post(
        "/api/v1/transactions",
        headers=h,
        json={
            "type": "EXPENSE",
            "amount_minor": amount,
            "currency_code": "NGN",
            "account_id": account["id"],
            "category_id": exp,
            "description": "Rent payment",
            "transaction_date": date.today().isoformat(),
        },
    ).json()["data"]


def test_mark_paid_links_expense(client: TestClient) -> None:
    h = auth_headers(client)
    bill = _create_bill(client, h, next_due_date=date.today().isoformat())
    occ = _occurrences(client, h, bill["id"])[0]
    tx = _expense(client, h)

    result = client.post(
        f"/api/v1/bill-occurrences/{occ['id']}/mark-paid",
        headers=h,
        json={"transaction_id": tx["id"]},
    ).json()["data"]
    assert result["status"] == "paid"
    assert result["settled_transaction_id"] == tx["id"]


def test_mark_paid_requires_expense(client: TestClient) -> None:
    h = auth_headers(client)
    bill = _create_bill(client, h, next_due_date=date.today().isoformat())
    occ = _occurrences(client, h, bill["id"])[0]
    account = create_account(client, h)
    inc = category_id(client, h, "INCOME")
    income = client.post(
        "/api/v1/transactions",
        headers=h,
        json={
            "type": "INCOME",
            "amount_minor": 100000,
            "currency_code": "NGN",
            "account_id": account["id"],
            "category_id": inc,
            "description": "Salary",
            "transaction_date": date.today().isoformat(),
        },
    ).json()["data"]

    resp = client.post(
        f"/api/v1/bill-occurrences/{occ['id']}/mark-paid",
        headers=h,
        json={"transaction_id": income["id"]},
    )
    assert resp.status_code == 400


def test_skip_occurrence(client: TestClient) -> None:
    h = auth_headers(client)
    bill = _create_bill(client, h, next_due_date=date.today().isoformat())
    occ = _occurrences(client, h, bill["id"])[0]
    result = client.post(f"/api/v1/bill-occurrences/{occ['id']}/skip", headers=h).json()["data"]
    assert result["status"] == "skipped"


def test_pause_bill_toggles(client: TestClient) -> None:
    h = auth_headers(client)
    bill = _create_bill(client, h)
    paused = client.post(f"/api/v1/bills/{bill['id']}/pause", headers=h).json()["data"]
    assert paused["status"] == "PAUSED"
    resumed = client.post(f"/api/v1/bills/{bill['id']}/pause", headers=h).json()["data"]
    assert resumed["status"] == "ACTIVE"
