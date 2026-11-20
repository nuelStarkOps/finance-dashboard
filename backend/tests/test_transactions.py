"""Financial correctness tests for the transaction/ledger engine."""

from fastapi.testclient import TestClient

from tests.utils import account_balance, auth_headers, category_id, create_account


def _income(client: TestClient, h: dict, account_id: str, amount: int, **extra) -> dict:
    payload = {
        "type": "INCOME",
        "amount_minor": amount,
        "currency_code": "NGN",
        "account_id": account_id,
        "category_id": category_id(client, h, "INCOME"),
        "description": "Salary",
        "transaction_date": "2026-01-05",
    }
    payload.update(extra)
    return client.post("/api/v1/transactions", headers=h, json=payload)


def _expense(client: TestClient, h: dict, account_id: str, amount: int, **extra) -> dict:
    payload = {
        "type": "EXPENSE",
        "amount_minor": amount,
        "currency_code": "NGN",
        "account_id": account_id,
        "category_id": category_id(client, h, "EXPENSE"),
        "description": "Groceries",
        "transaction_date": "2026-01-06",
    }
    payload.update(extra)
    return client.post("/api/v1/transactions", headers=h, json=payload)


def _transfer(client: TestClient, h: dict, source: str, dest: str, amount: int) -> dict:
    return client.post(
        "/api/v1/transactions",
        headers=h,
        json={
            "type": "TRANSFER",
            "amount_minor": amount,
            "currency_code": "NGN",
            "source_account_id": source,
            "destination_account_id": dest,
            "description": "Move to savings",
            "transaction_date": "2026-01-07",
        },
    )


def test_income_increases_balance(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, balance=0)
    resp = _income(client, h, account["id"], 10000)
    assert resp.status_code == 200
    assert account_balance(client, h, account["id"]) == 10000


def test_expense_decreases_balance(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, balance=10000)
    resp = _expense(client, h, account["id"], 3000)
    assert resp.status_code == 200
    assert account_balance(client, h, account["id"]) == 7000


def test_transfer_updates_both_accounts_atomically(client: TestClient) -> None:
    h = auth_headers(client)
    source = create_account(client, h, name="Bank", balance=5000)
    dest = create_account(client, h, name="Savings", balance=0)
    resp = _transfer(client, h, source["id"], dest["id"], 2000)
    assert resp.status_code == 200
    assert account_balance(client, h, source["id"]) == 3000
    assert account_balance(client, h, dest["id"]) == 2000


def test_transfer_same_account_rejected(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, balance=5000)
    resp = _transfer(client, h, account["id"], account["id"], 1000)
    assert resp.status_code == 400


def test_transfer_cross_currency_rejected(client: TestClient) -> None:
    h = auth_headers(client)
    ngn = create_account(client, h, name="NGN", currency="NGN", balance=5000)
    usd = create_account(client, h, name="USD", currency="USD", balance=100)
    resp = _transfer(client, h, ngn["id"], usd["id"], 1000)
    assert resp.status_code == 400


def test_void_excludes_transaction_from_balance(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, balance=0)
    tx = _income(client, h, account["id"], 10000).json()["data"]
    assert account_balance(client, h, account["id"]) == 10000

    voided = client.post(f"/api/v1/transactions/{tx['id']}/void", headers=h).json()["data"]
    assert voided["status"] == "VOIDED"
    assert account_balance(client, h, account["id"]) == 0


def test_edit_reverses_and_reposts(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, balance=10000)
    original = _expense(client, h, account["id"], 3000).json()["data"]
    assert account_balance(client, h, account["id"]) == 7000

    corrected = client.patch(
        f"/api/v1/transactions/{original['id']}",
        headers=h,
        json={
            "type": "EXPENSE",
            "amount_minor": 1000,
            "currency_code": "NGN",
            "account_id": account["id"],
            "category_id": category_id(client, h, "EXPENSE"),
            "description": "Groceries (corrected)",
            "transaction_date": "2026-01-06",
        },
    ).json()["data"]
    assert corrected["status"] == "POSTED"
    assert corrected["amount_minor"] == 1000
    assert account_balance(client, h, account["id"]) == 9000

    # The original is now voided.
    orig = client.get(f"/api/v1/transactions/{original['id']}", headers=h).json()["data"]
    assert orig["status"] == "VOIDED"


def test_idempotency_prevents_duplicate(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, balance=0)

    first = client.post(
        "/api/v1/transactions",
        headers={**h, "Idempotency-Key": "dup-key-1"},
        json={
            "type": "INCOME",
            "amount_minor": 5000,
            "currency_code": "NGN",
            "account_id": account["id"],
            "category_id": category_id(client, h, "INCOME"),
            "description": "Salary",
            "transaction_date": "2026-01-05",
        },
    ).json()["data"]

    second = client.post(
        "/api/v1/transactions",
        headers={**h, "Idempotency-Key": "dup-key-1"},
        json={
            "type": "INCOME",
            "amount_minor": 5000,
            "currency_code": "NGN",
            "account_id": account["id"],
            "category_id": category_id(client, h, "INCOME"),
            "description": "Salary",
            "transaction_date": "2026-01-05",
        },
    ).json()["data"]

    assert first["id"] == second["id"]
    assert account_balance(client, h, account["id"]) == 5000


def test_archived_account_rejects_transaction(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, balance=0)
    client.post(f"/api/v1/accounts/{account['id']}/archive", headers=h)
    resp = _income(client, h, account["id"], 1000)
    assert resp.status_code == 400


def test_cross_user_account_rejected(client: TestClient) -> None:
    h_a = auth_headers(client, email="a@example.com")
    account_a = create_account(client, h_a)
    h_b = auth_headers(client, email="b@example.com", name="Bob")
    resp = _income(client, h_b, account_a["id"], 1000)
    assert resp.status_code == 403


def test_ledger_entry_signs(client: TestClient) -> None:
    h = auth_headers(client)
    source = create_account(client, h, name="Bank", balance=0)
    dest = create_account(client, h, name="Savings", balance=0)

    income = _income(client, h, source["id"], 10000).json()["data"]
    assert income["ledger_entries"][0]["amount_minor"] == 10000

    expense = _expense(client, h, source["id"], 3000).json()["data"]
    assert expense["ledger_entries"][0]["amount_minor"] == -3000

    transfer = _transfer(client, h, source["id"], dest["id"], 2000).json()["data"]
    amounts = sorted(e["amount_minor"] for e in transfer["ledger_entries"])
    assert amounts == [-2000, 2000]


def test_list_filters_by_type(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, balance=0)
    _income(client, h, account["id"], 10000)
    _expense(client, h, account["id"], 3000)

    incomes = client.get("/api/v1/transactions", headers=h, params={"type": "INCOME"}).json()[
        "data"
    ]
    assert len(incomes) == 1
    assert incomes[0]["type"] == "INCOME"


def test_category_type_mismatch_rejected(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, balance=0)
    resp = _income(
        client,
        h,
        account["id"],
        1000,
        category_id=category_id(client, h, "EXPENSE"),
    )
    assert resp.status_code == 400


def test_amount_must_be_positive(client: TestClient) -> None:
    h = auth_headers(client)
    account = create_account(client, h, balance=0)
    resp = _income(client, h, account["id"], -100)
    assert resp.status_code == 422
