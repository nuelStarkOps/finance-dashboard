"""Report endpoints — deterministic financial analytics and export."""

import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services import reports as reports_service

router = APIRouter(tags=["reports"])


@router.get("/reports/cashflow")
def cashflow(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    currency: str | None = Query(default=None, pattern=r"^[A-Z]{3}$"),
    group: str = Query(default="month", pattern="^(day|month)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    currency = currency or reports_service.preferred_currency(db, user)
    return ok(reports_service.cashflow(db, user, currency, from_date, to_date, group))


@router.get("/reports/spending")
def spending(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    currency: str | None = Query(default=None, pattern=r"^[A-Z]{3}$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    currency = currency or reports_service.preferred_currency(db, user)
    return ok(reports_service.spending(db, user, currency, from_date, to_date))


@router.get("/reports/income")
def income(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    currency: str | None = Query(default=None, pattern=r"^[A-Z]{3}$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    currency = currency or reports_service.preferred_currency(db, user)
    return ok(reports_service.income(db, user, currency, from_date, to_date))


@router.get("/reports/savings-rate")
def savings_rate(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    currency: str | None = Query(default=None, pattern=r"^[A-Z]{3}$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    currency = currency or reports_service.preferred_currency(db, user)
    return ok(reports_service.savings_rate(db, user, currency, from_date, to_date))


@router.get("/reports/monthly-comparison")
def monthly_comparison(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    currency: str | None = Query(default=None, pattern=r"^[A-Z]{3}$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    currency = currency or reports_service.preferred_currency(db, user)
    return ok(reports_service.monthly_comparison(db, user, currency, from_date, to_date))


@router.get("/reports/budgets")
def budgets(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(reports_service.budget_performance(db, user))


@router.get("/reports/insights")
def insights(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    currency: str | None = Query(default=None, pattern=r"^[A-Z]{3}$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    currency = currency or reports_service.preferred_currency(db, user)
    return ok(reports_service.insights(db, user, currency, from_date, to_date))


class ExportRequest(BaseModel):
    from_: date | None = None
    to: date | None = None
    currency: str | None = None


@router.post("/reports/export")
def export_report(
    payload: ExportRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Generate a CSV report (summary, monthly cashflow, spending breakdown)."""
    currency = payload.currency or reports_service.preferred_currency(db, user)
    summary = reports_service.savings_rate(db, user, currency, payload.from_, payload.to)
    cashflow = reports_service.monthly_comparison(db, user, currency, payload.from_, payload.to)
    spending = reports_service.spending(db, user, currency, payload.from_, payload.to)

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["Personal Finance OS — report", currency])
    writer.writerow([])
    writer.writerow(["Summary"])
    writer.writerow(["income_minor", "expenses_minor", "net_minor", "savings_rate_percent"])
    writer.writerow(
        [
            summary["income_minor"],
            summary["expenses_minor"],
            summary["net_minor"],
            summary["savings_rate_percent"],
        ]
    )
    writer.writerow([])
    writer.writerow(["Monthly cash flow"])
    writer.writerow(["period", "income_minor", "expenses_minor", "net_minor"])
    for row in cashflow:
        writer.writerow(
            [row["period"], row["income_minor"], row["expenses_minor"], row["net_minor"]]
        )
    writer.writerow([])
    writer.writerow(["Spending by category"])
    writer.writerow(["category", "total_minor", "percent"])
    for row in spending:
        writer.writerow([row["name"], row["total_minor"], row["percent"]])

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="pfos-report.csv"'},
    )
