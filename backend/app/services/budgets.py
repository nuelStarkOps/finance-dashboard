"""Budget service — CRUD, archive and usage calculation.

Usage counts only POSTED expense transactions within the budget's date range and
currency. An overall budget tracks all expenses; category items track their own
category. Spending is never double-counted: a budget with category items only
measures the budgeted categories, while an overall limit measures all expenses.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.budget import Budget, BudgetItem
from app.models.category import Category
from app.models.enums import BudgetStatus, TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetUpdate

WARNING_PERCENT = 80.0
OVER_PERCENT = 100.0


def _load(db: Session, budget_id: uuid.UUID) -> Budget | None:
    return (
        db.query(Budget)
        .options(selectinload(Budget.items).selectinload(BudgetItem.category))
        .filter(Budget.id == budget_id)
        .one_or_none()
    )


def _owned(db: Session, user: User, budget_id: uuid.UUID) -> Budget:
    budget = _load(db, budget_id)
    if budget is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Budget not found")
    if budget.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Budget does not belong to you")
    return budget


def _expense_query(db: Session, user: User, currency: str, start, end):
    return db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.currency_code == currency,
        Transaction.type == TransactionType.EXPENSE.value,
        Transaction.status == TransactionStatus.POSTED.value,
        Transaction.transaction_date >= start,
        Transaction.transaction_date <= end,
    )


def _spending_total(db: Session, user: User, currency: str, start, end) -> int:
    return int(
        _expense_query(db, user, currency, start, end)
        .with_entities(func.coalesce(func.sum(Transaction.amount_minor), 0))
        .scalar()
        or 0
    )


def _spending_by_category(
    db: Session, user: User, currency: str, start, end
) -> dict[uuid.UUID, int]:
    rows = (
        _expense_query(db, user, currency, start, end)
        .with_entities(Transaction.category_id, func.sum(Transaction.amount_minor))
        .group_by(Transaction.category_id)
        .all()
    )
    return {cid: int(total) for cid, total in rows if cid is not None}


def _usage(spent: int, limit: int | None) -> float | None:
    if limit is None or limit <= 0:
        return None
    return round((spent / limit) * 100, 1)


def _status_for(percent: float | None) -> str:
    if percent is None:
        return "ok"
    if percent >= OVER_PERCENT:
        return "over"
    if percent >= WARNING_PERCENT:
        return "warning"
    return "ok"


def _validate_items(db: Session, user: User, items) -> list[BudgetItem]:
    result = []
    for item in items:
        category = db.get(Category, item.category_id)
        if category is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
        if category.user_id is not None and category.user_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Category does not belong to you")
        if category.type != "EXPENSE":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Budget categories must be expense categories"
            )
        result.append(BudgetItem(category_id=item.category_id, limit_minor=item.limit_minor))
    return result


def create_budget(db: Session, user: User, payload: BudgetCreate) -> Budget:
    budget = Budget(
        user_id=user.id,
        name=payload.name,
        currency_code=payload.currency_code,
        start_date=payload.start_date,
        end_date=payload.end_date,
        total_limit_minor=payload.total_limit_minor,
        status=BudgetStatus.ACTIVE.value,
    )
    budget.items = _validate_items(db, user, payload.items)
    db.add(budget)
    db.commit()
    return _load(db, budget.id)


def list_budgets(db: Session, user: User) -> list[Budget]:
    return (
        db.query(Budget)
        .options(selectinload(Budget.items).selectinload(BudgetItem.category))
        .filter(Budget.user_id == user.id)
        .order_by(Budget.start_date.desc())
        .all()
    )


def get_budget(db: Session, user: User, budget_id: uuid.UUID) -> Budget:
    return _owned(db, user, budget_id)


def update_budget(db: Session, user: User, budget_id: uuid.UUID, payload: BudgetUpdate) -> Budget:
    budget = _owned(db, user, budget_id)
    if payload.name is not None:
        budget.name = payload.name
    if payload.start_date is not None:
        budget.start_date = payload.start_date
    if payload.end_date is not None:
        budget.end_date = payload.end_date
    if payload.total_limit_minor is not None:
        budget.total_limit_minor = payload.total_limit_minor
    if budget.end_date < budget.start_date:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "end_date must be on or after start_date")
    db.commit()
    return _load(db, budget.id)


def archive_budget(db: Session, user: User, budget_id: uuid.UUID) -> Budget:
    budget = _owned(db, user, budget_id)
    budget.status = BudgetStatus.ARCHIVED.value
    db.commit()
    return _load(db, budget.id)


def performance(db: Session, user: User, budget_id: uuid.UUID) -> dict:
    budget = _owned(db, user, budget_id)
    total_spent = _spending_total(
        db, user, budget.currency_code, budget.start_date, budget.end_date
    )
    by_category = _spending_by_category(
        db, user, budget.currency_code, budget.start_date, budget.end_date
    )

    total_limit = budget.total_limit_minor
    total_usage = _usage(total_spent, total_limit)

    items = []
    for item in budget.items:
        spent = by_category.get(item.category_id, 0)
        usage = _usage(spent, item.limit_minor)
        items.append(
            {
                "category_id": str(item.category_id),
                "name": item.category.name,
                "color": item.category.color,
                "limit_minor": item.limit_minor,
                "spent_minor": spent,
                "remaining_minor": item.limit_minor - spent,
                "usage_percent": usage,
                "status": _status_for(usage),
            }
        )

    return {
        "budget_id": str(budget.id),
        "name": budget.name,
        "currency_code": budget.currency_code,
        "start_date": budget.start_date.isoformat(),
        "end_date": budget.end_date.isoformat(),
        "total_limit_minor": total_limit,
        "total_spent_minor": total_spent,
        "total_remaining_minor": total_limit - total_spent if total_limit is not None else None,
        "total_usage_percent": total_usage,
        "status": _status_for(total_usage),
        "items": items,
    }


def overview(db: Session, user: User) -> list[dict]:
    """Lightweight progress rows for the dashboard budget section."""
    budgets = (
        db.query(Budget)
        .options(selectinload(Budget.items))
        .filter(Budget.user_id == user.id, Budget.status == BudgetStatus.ACTIVE.value)
        .order_by(Budget.start_date.desc())
        .all()
    )
    result = []
    for budget in budgets:
        total_spent = _spending_total(
            db, user, budget.currency_code, budget.start_date, budget.end_date
        )
        by_category = _spending_by_category(
            db, user, budget.currency_code, budget.start_date, budget.end_date
        )

        if budget.total_limit_minor is not None:
            limit = budget.total_limit_minor
            spent = total_spent
        else:
            limit = sum(i.limit_minor for i in budget.items)
            spent = sum(by_category.get(i.category_id, 0) for i in budget.items)

        usage = _usage(spent, limit)
        result.append(
            {
                "budget_id": str(budget.id),
                "name": budget.name,
                "currency_code": budget.currency_code,
                "limit_minor": limit,
                "spent_minor": spent,
                "usage_percent": usage,
                "status": _status_for(usage),
            }
        )
    return result
