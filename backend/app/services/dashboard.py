"""Dashboard service — server-side aggregation for the overview dashboard.

Aggregations are computed here (not in the browser) and are deterministic from
the underlying ledger. Balances are derived from opening balances + posted
ledger entries; voided transactions are excluded.
"""

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.account import Account
from app.models.enums import AccountStatus, TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.models.user import User, UserPreference
from app.services.ledger import posted_total


def preferred_currency(db: Session, user: User) -> str:
    prefs = db.get(UserPreference, user.id)
    return prefs.preferred_currency if prefs else "NGN"


def _account_balance(db: Session, account: Account) -> int:
    return account.opening_balance_minor + posted_total(db, account.id)


def _sum_transactions(
    db: Session,
    user: User,
    type_: str,
    currency: str,
    from_date: date | None,
    to_date: date | None,
) -> int:
    query = db.query(func.coalesce(func.sum(Transaction.amount_minor), 0)).filter(
        Transaction.user_id == user.id,
        Transaction.type == type_,
        Transaction.currency_code == currency,
        Transaction.status == TransactionStatus.POSTED.value,
    )
    if from_date:
        query = query.filter(Transaction.transaction_date >= from_date)
    if to_date:
        query = query.filter(Transaction.transaction_date <= to_date)
    return int(query.scalar() or 0)


def summary(
    db: Session,
    user: User,
    from_date: date | None,
    to_date: date | None,
    currency: str | None = None,
) -> dict:
    currency = currency or preferred_currency(db, user)

    accounts = (
        db.query(Account)
        .filter(
            Account.user_id == user.id,
            Account.currency_code == currency,
            Account.status == AccountStatus.ACTIVE.value,
        )
        .all()
    )
    total_balance = sum(_account_balance(db, a) for a in accounts)

    income = _sum_transactions(db, user, TransactionType.INCOME.value, currency, from_date, to_date)
    expenses = _sum_transactions(
        db, user, TransactionType.EXPENSE.value, currency, from_date, to_date
    )

    return {
        "currency_code": currency,
        "total_balance_minor": total_balance,
        "income_minor": income,
        "expenses_minor": expenses,
        "net_cashflow_minor": income - expenses,
        "period": {
            "from": from_date.isoformat() if from_date else None,
            "to": to_date.isoformat() if to_date else None,
        },
    }


def cashflow(
    db: Session,
    user: User,
    from_date: date | None,
    to_date: date | None,
    currency: str | None,
    group: str = "day",
) -> list[dict]:
    currency = currency or preferred_currency(db, user)
    query = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.currency_code == currency,
        Transaction.status == TransactionStatus.POSTED.value,
        Transaction.type.in_([TransactionType.INCOME.value, TransactionType.EXPENSE.value]),
    )
    if from_date:
        query = query.filter(Transaction.transaction_date >= from_date)
    if to_date:
        query = query.filter(Transaction.transaction_date <= to_date)

    buckets: dict[str, dict[str, int]] = {}
    for tx in query.all():
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

    return [{"period": key, **values} for key, values in sorted(buckets.items())]


def spending(
    db: Session,
    user: User,
    from_date: date | None,
    to_date: date | None,
    currency: str | None,
) -> list[dict]:
    currency = currency or preferred_currency(db, user)
    query = (
        db.query(Transaction)
        .options(selectinload(Transaction.category))
        .filter(
            Transaction.user_id == user.id,
            Transaction.currency_code == currency,
            Transaction.status == TransactionStatus.POSTED.value,
            Transaction.type == TransactionType.EXPENSE.value,
        )
    )
    if from_date:
        query = query.filter(Transaction.transaction_date >= from_date)
    if to_date:
        query = query.filter(Transaction.transaction_date <= to_date)

    by_category: dict[str, dict] = {}
    for tx in query.all():
        if tx.category is not None:
            key = str(tx.category.id)
            if key not in by_category:
                by_category[key] = {
                    "category_id": str(tx.category.id),
                    "name": tx.category.name,
                    "color": tx.category.color,
                    "total_minor": 0,
                }
            by_category[key]["total_minor"] += tx.amount_minor

    return sorted(by_category.values(), key=lambda c: -c["total_minor"])


def recent_transactions(db: Session, user: User, limit: int = 5) -> list[Transaction]:
    return (
        db.query(Transaction)
        .options(
            selectinload(Transaction.category),
            selectinload(Transaction.ledger_entries),
        )
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .limit(limit)
        .all()
    )


def account_overview(db: Session, user: User) -> list[dict]:
    accounts = (
        db.query(Account)
        .filter(Account.user_id == user.id)
        .order_by(Account.created_at.desc())
        .all()
    )
    result = []
    for account in accounts:
        result.append(
            {
                "id": str(account.id),
                "name": account.name,
                "account_type": account.account_type,
                "currency_code": account.currency_code,
                "status": account.status,
                "balance_minor": _account_balance(db, account),
            }
        )
    return result


def budget_overview(db: Session, user: User) -> list[dict]:
    """Budget progress — implemented in Phase 4. Returns an empty list for now."""
    return []
