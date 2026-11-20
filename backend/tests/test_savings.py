"""Savings goal tests."""

from datetime import date

from fastapi.testclient import TestClient

from tests.utils import auth_headers


def _create_goal(client: TestClient, h: dict, target: int = 100000) -> dict:
    return client.post(
        "/api/v1/savings/goals",
        headers=h,
        json={
            "name": "Emergency fund",
            "currency_code": "NGN",
            "target_minor": target,
            "target_date": "2026-12-31",
        },
    ).json()["data"]


def _contribute(
    client: TestClient, h: dict, goal_id: str, amount: int, ctype: str = "CONTRIBUTION"
) -> None:
    client.post(
        f"/api/v1/savings/goals/{goal_id}/contributions",
        headers=h,
        json={
            "amount_minor": amount,
            "contribution_type": ctype,
            "contribution_date": date.today().isoformat(),
        },
    )


def test_create_goal(client: TestClient) -> None:
    h = auth_headers(client)
    goal = _create_goal(client, h)
    assert goal["name"] == "Emergency fund"
    assert goal["allocated_minor"] == 0
    assert goal["progress_percent"] == 0.0


def test_goal_progress_contributions_minus_withdrawals(client: TestClient) -> None:
    h = auth_headers(client)
    goal = _create_goal(client, h, target=100000)
    _contribute(client, h, goal["id"], 30000)
    _contribute(client, h, goal["id"], 10000, ctype="WITHDRAWAL")

    data = client.get(f"/api/v1/savings/goals/{goal['id']}", headers=h).json()["data"]
    assert data["allocated_minor"] == 20000
    assert data["progress_percent"] == 20.0


def test_overfunded_goal_not_clamped(client: TestClient) -> None:
    h = auth_headers(client)
    goal = _create_goal(client, h, target=10000)
    _contribute(client, h, goal["id"], 15000)
    data = client.get(f"/api/v1/savings/goals/{goal['id']}", headers=h).json()["data"]
    assert data["allocated_minor"] == 15000
    assert data["progress_percent"] == 150.0


def test_negative_target_rejected(client: TestClient) -> None:
    h = auth_headers(client)
    resp = client.post(
        "/api/v1/savings/goals",
        headers=h,
        json={"name": "Bad", "currency_code": "NGN", "target_minor": 0},
    )
    assert resp.status_code == 422


def test_contribution_history(client: TestClient) -> None:
    h = auth_headers(client)
    goal = _create_goal(client, h)
    _contribute(client, h, goal["id"], 1000)
    _contribute(client, h, goal["id"], 2000)
    history = client.get(f"/api/v1/savings/goals/{goal['id']}/history", headers=h).json()["data"]
    assert len(history) == 2
    assert {c["amount_minor"] for c in history} == {1000, 2000}


def test_goal_isolation(client: TestClient) -> None:
    h_a = auth_headers(client, email="a@example.com")
    goal_a = _create_goal(client, h_a)
    h_b = auth_headers(client, email="b@example.com", name="Bob")
    resp = client.get(f"/api/v1/savings/goals/{goal_a['id']}", headers=h_b)
    assert resp.status_code == 403
