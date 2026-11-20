"""Reports service — deterministic aggregations and insights.

All values are computed from posted transactions (transfers excluded from
income/expense), so every report is reproducible from the underlying records.
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session, selectinload

from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.models.user import User, UserPreference
from app.services import budgets as budgets_service


def preferred_currency(db: Session, user: User) -> str:
    prefs = db.get(UserPreference, user.id)
    return prefs.preferred_currency if prefs else "NGN"


def _transactions(
    db: Session,
    user: User,
    currency: str,
    from_date: date | None,
    to_date: date | None,
    types: list[str],
) -> list[Transaction]:
    query = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.currency_code == currency,
        Transaction.status == TransactionStatus.POSTED.value,
        Transaction.type.in_(types),
    )
    if from_date:
        query = query.filter(Transaction.transaction_date >= from_date)
    if to_date:
        query = query.filter(Transaction.transaction_date <= to_date)
    return query.all()


def _sum_by_type(txs: list[Transaction]) -> tuple[int, int]:
    income = sum(t.amount_minor for t in txs if t.type == TransactionType.INCOME.value)
    expenses = sum(t.amount_minor for t in txs if t.type == TransactionType.EXPENSE.value)
    return income, expenses


def cashflow(
    db: Session,
    user: User,
    currency: str,
    from_date: date | None,
    to_date: date | None,
    group: str = "month",
) -> list[dict]:
    txs = _transactions(
        db,
        user,
        currency,
        from_date,
        to_date,
        [TransactionType.INCOME.value, TransactionType.EXPENSE.value],
    )
    buckets: dict[str, dict[str, int]] = {}
    for tx in txs:
        key = (
            tx.transaction_date.strftime("%Y-%m")
            if group == "month"
            else tx.transaction_date.isoformat()
        )
        bucket = buckets.setdefault(key, {"income_minor": 0, "expenses_minor": 0})
        if tx.type == TransactionType.INCOME.value:
            bucket["income_minor"] += tx.amount_minor
        else:
            bucket["expenses_minor"] += tx.amount_minor

    return [
        {
            "period": key,
            "income_minor": v["income_minor"],
            "expenses_minor": v["expenses_minor"],
            "net_minor": v["income_minor"] - v["expenses_minor"],
        }
        for key, v in sorted(buckets.items())
    ]


def _category_breakdown(
    db: Session,
    user: User,
    currency: str,
    from_date: date | None,
    to_date: date | None,
    type_: str,
) -> list[dict]:
    txs = (
        db.query(Transaction)
        .options(selectinload(Transaction.category))
        .filter(
            Transaction.user_id == user.id,
            Transaction.currency_code == currency,
            Transaction.status == TransactionStatus.POSTED.value,
            Transaction.type == type_,
        )
    )
    if from_date:
        txs = txs.filter(Transaction.transaction_date >= from_date)
    if to_date:
        txs = txs.filter(Transaction.transaction_date <= to_date)

    by_category: dict[str, dict] = {}
    total = 0
    for tx in txs.all():
        name = tx.category.name if tx.category else "Uncategorised"
        key = name
        if key not in by_category:
            by_category[key] = {
                "category_id": str(tx.category.id) if tx.category else None,
                "name": name,
                "color": tx.category.color if tx.category else None,
                "total_minor": 0,
            }
        by_category[key]["total_minor"] += tx.amount_minor
        total += tx.amount_minor

    result = sorted(by_category.values(), key=lambda c: -c["total_minor"])
    for item in result:
        item["percent"] = round((item["total_minor"] / total) * 100, 1) if total else 0.0
    return result


def spending(db, user, currency, from_date, to_date) -> list[dict]:
    return _category_breakdown(
        db, user, currency, from_date, to_date, TransactionType.EXPENSE.value
    )


def income(db, user, currency, from_date, to_date) -> list[dict]:
    return _category_breakdown(db, user, currency, from_date, to_date, TransactionType.INCOME.value)


def savings_rate(
    db: Session,
    user: User,
    currency: str,
    from_date: date | None,
    to_date: date | None,
) -> dict:
    txs = _transactions(
        db,
        user,
        currency,
        from_date,
        to_date,
        [TransactionType.INCOME.value, TransactionType.EXPENSE.value],
    )
    income_minor, expenses_minor = _sum_by_type(txs)
    net = income_minor - expenses_minor
    rate = round((net / income_minor) * 100, 1) if income_minor > 0 else None
    return {
        "income_minor": income_minor,
        "expenses_minor": expenses_minor,
        "net_minor": net,
        "savings_rate_percent": rate,
    }


def monthly_comparison(db, user, currency, from_date, to_date) -> list[dict]:
    return cashflow(db, user, currency, from_date, to_date, group="month")


def budget_performance(db: Session, user: User) -> list[dict]:
    return budgets_service.overview(db, user)


def insights(
    db: Session,
    user: User,
    currency: str,
    from_date: date | None,
    to_date: date | None,
) -> list[dict]:
    """Deterministic, rule-based insights (no AI)."""
    result: list[dict] = []

    rate = savings_rate(db, user, currency, from_date, to_date)
    income_minor = rate["income_minor"]
    expenses_minor = rate["expenses_minor"]

    if income_minor == 0 and expenses_minor == 0:
        return [
            {
                "type": "no_data",
                "title": "No activity in this period",
                "message": "Record income and expenses to see insights.",
                "severity": "info",
            }
        ]

    if rate["net_minor"] < 0:
        result.append(
            {
                "type": "cashflow",
                "title": "Spending exceeded income",
                "message": "You spent more than you earned in this period.",
                "severity": "warning",
            }
        )
    else:
        result.append(
            {
                "type": "cashflow",
                "title": "Positive cash flow",
                "message": "Your income exceeded expenses in this period.",
                "severity": "positive",
            }
        )

    if rate["savings_rate_percent"] is not None:
        result.append(
            {
                "type": "savings_rate",
                "title": f"Savings rate {rate['savings_rate_percent']}%",
                "message": "Percentage of income left after expenses.",
                "severity": "info",
            }
        )

    # Top spending category.
    spend = spending(db, user, currency, from_date, to_date)
    if spend:
        top = spend[0]
        result.append(
            {
                "type": "top_category",
                "title": f"Top spending: {top['name']}",
                "message": f"{top['name']} was {top['percent']}% of your spending.",
                "severity": "info",
            }
        )

    # Month-over-month expense change (requires a bounded range).
    if from_date and to_date:
        length = (to_date - from_date).days + 1
        prev_to = from_date - timedelta(days=1)
        prev_from = prev_to - timedelta(days=length - 1)
        prev_txs = _transactions(
            db,
            user,
            currency,
            prev_from,
            prev_to,
            [TransactionType.EXPENSE.value],
        )
        prev_expenses = sum(t.amount_minor for t in prev_txs)
        if prev_expenses > 0:
            change = round(((expenses_minor - prev_expenses) / prev_expenses) * 100, 1)
            direction = "up" if change >= 0 else "down"
            result.append(
                {
                    "type": "trend",
                    "title": f"Spending {direction} {abs(change)}%",
                    "message": "Compared with the previous period.",
                    "severity": "warning" if change > 10 else "info",
                }
            )

    return result
