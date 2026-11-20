"""Dashboard endpoints — aggregated metrics for the overview screen."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transaction import TransactionOut
from app.services import dashboard as dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary")
def summary(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    currency: str | None = Query(default=None, pattern=r"^[A-Z]{3}$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = dashboard_service.summary(db, user, from_date, to_date, currency)
    return ok(data)


@router.get("/dashboard/cashflow")
def cashflow(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    currency: str | None = Query(default=None, pattern=r"^[A-Z]{3}$"),
    group: str = Query(default="day", pattern="^(day|month)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = dashboard_service.cashflow(db, user, from_date, to_date, currency, group)
    return ok(data)


@router.get("/dashboard/spending")
def spending(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    currency: str | None = Query(default=None, pattern=r"^[A-Z]{3}$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = dashboard_service.spending(db, user, from_date, to_date, currency)
    return ok(data)


@router.get("/dashboard/recent-transactions")
def recent_transactions(
    limit: int = Query(default=5, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items = dashboard_service.recent_transactions(db, user, limit)
    data = [TransactionOut.model_validate(t).model_dump(mode="json") for t in items]
    return ok(data)


@router.get("/dashboard/account-overview")
def account_overview(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(dashboard_service.account_overview(db, user))


@router.get("/dashboard/budget-overview")
def budget_overview(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(dashboard_service.budget_overview(db, user))
