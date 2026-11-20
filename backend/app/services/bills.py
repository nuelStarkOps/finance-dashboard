"""Recurring bills service — schedules, occurrences and payment lifecycle.

A bill is considered paid only after the user records a posted expense
transaction and links it to an occurrence. Occurrence statuses (upcoming / due /
overdue) are derived from the due date; paid / skipped are explicit.
"""

import calendar
import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.models.bill import BillOccurrence, RecurringBill
from app.models.category import Category
from app.models.enums import (
    BillStatus,
    OccurrenceStatus,
    TransactionStatus,
    TransactionType,
)
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.bill import BillCreate, BillUpdate

OCCURRENCE_COUNT = 12


def _add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def advance_from(original: date, frequency: str, interval: int, index: int) -> date:
    """Compute the ``index``-th due date, anchored on the original day-of-month.

    Month-based frequencies keep the original day (clamped to month-end), so a
    bill due on the 31st yields Jan 31, Feb 28, Mar 31, Apr 30, ...
    """
    if frequency == "WEEKLY":
        return original + timedelta(weeks=interval * index)
    if frequency == "MONTHLY":
        return _add_months(original, interval * index)
    if frequency == "QUARTERLY":
        return _add_months(original, interval * 3 * index)
    if frequency == "ANNUALLY":
        return _add_months(original, interval * 12 * index)
    # CUSTOM: interval is days
    return original + timedelta(days=interval * index)


def effective_status(occ: BillOccurrence, today: date) -> str:
    if occ.status == OccurrenceStatus.PAID.value:
        return "paid"
    if occ.status == OccurrenceStatus.SKIPPED.value:
        return "skipped"
    if occ.due_date < today:
        return "overdue"
    if occ.due_date == today:
        return "due"
    return "upcoming"


def _load(db: Session, bill_id: uuid.UUID) -> RecurringBill | None:
    return (
        db.query(RecurringBill)
        .options(selectinload(RecurringBill.category))
        .filter(RecurringBill.id == bill_id)
        .one_or_none()
    )


def _owned(db: Session, user: User, bill_id: uuid.UUID) -> RecurringBill:
    bill = _load(db, bill_id)
    if bill is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bill not found")
    if bill.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bill does not belong to you")
    return bill


def _owned_occurrence(db: Session, user: User, occurrence_id: uuid.UUID) -> BillOccurrence:
    occ = db.get(BillOccurrence, occurrence_id)
    if occ is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Occurrence not found")
    if occ.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Occurrence does not belong to you")
    return occ


def _validate_category(db: Session, user: User, category_id: uuid.UUID | None) -> None:
    if category_id is None:
        return
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    if category.user_id is not None and category.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Category does not belong to you")
    if category.type != "EXPENSE":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Bill category must be an expense category"
        )


def _generate_occurrences(
    bill: RecurringBill, count: int = OCCURRENCE_COUNT
) -> list[BillOccurrence]:
    occurrences = []
    for i in range(count):
        due = advance_from(bill.next_due_date, bill.frequency, bill.interval_value, i)
        occurrences.append(
            BillOccurrence(
                user_id=bill.user_id,
                due_date=due,
                amount_minor=bill.amount_minor,
                status=OccurrenceStatus.PENDING.value,
            )
        )
    return occurrences


def _refresh_next_due(db: Session, bill: RecurringBill, today: date) -> None:
    next_occ = (
        db.query(BillOccurrence)
        .filter(
            BillOccurrence.bill_id == bill.id,
            BillOccurrence.status == OccurrenceStatus.PENDING.value,
            BillOccurrence.due_date >= today,
        )
        .order_by(BillOccurrence.due_date)
        .first()
    )
    if next_occ is not None:
        bill.next_due_date = next_occ.due_date


def create_bill(db: Session, user: User, payload: BillCreate) -> RecurringBill:
    _validate_category(db, user, payload.category_id)
    bill = RecurringBill(
        user_id=user.id,
        name=payload.name,
        amount_minor=payload.amount_minor,
        currency_code=payload.currency_code,
        category_id=payload.category_id,
        frequency=payload.frequency,
        interval_value=payload.interval_value,
        next_due_date=payload.next_due_date,
        reminder_days=payload.reminder_days,
        status=BillStatus.ACTIVE.value,
    )
    bill.occurrences = _generate_occurrences(bill)
    db.add(bill)
    db.commit()
    return _load(db, bill.id)


def list_bills(db: Session, user: User) -> list[RecurringBill]:
    return (
        db.query(RecurringBill)
        .options(selectinload(RecurringBill.category))
        .filter(RecurringBill.user_id == user.id)
        .order_by(RecurringBill.next_due_date)
        .all()
    )


def get_bill(db: Session, user: User, bill_id: uuid.UUID) -> RecurringBill:
    return _owned(db, user, bill_id)


def update_bill(db: Session, user: User, bill_id: uuid.UUID, payload: BillUpdate) -> RecurringBill:
    bill = _owned(db, user, bill_id)
    if payload.name is not None:
        bill.name = payload.name
    if payload.amount_minor is not None:
        bill.amount_minor = payload.amount_minor
    if payload.category_id is not None:
        _validate_category(db, user, payload.category_id)
        bill.category_id = payload.category_id
    if payload.reminder_days is not None:
        bill.reminder_days = payload.reminder_days
    db.commit()
    return _load(db, bill.id)


def pause_bill(db: Session, user: User, bill_id: uuid.UUID) -> RecurringBill:
    bill = _owned(db, user, bill_id)
    bill.status = (
        BillStatus.ACTIVE.value
        if bill.status == BillStatus.PAUSED.value
        else BillStatus.PAUSED.value
    )
    db.commit()
    return _load(db, bill.id)


def list_occurrences(
    db: Session, user: User, bill_id: uuid.UUID, status_filter: str | None = None
) -> list[dict]:
    _owned(db, user, bill_id)
    today = date.today()
    occurrences = (
        db.query(BillOccurrence)
        .filter(BillOccurrence.bill_id == bill_id)
        .order_by(BillOccurrence.due_date)
        .all()
    )
    result = []
    for occ in occurrences:
        status_ = effective_status(occ, today)
        if status_filter and status_ != status_filter:
            continue
        result.append(
            {
                "id": str(occ.id),
                "due_date": occ.due_date.isoformat(),
                "amount_minor": occ.amount_minor,
                "status": status_,
                "paid_at": occ.paid_at.isoformat() if occ.paid_at else None,
                "settled_transaction_id": str(occ.settled_transaction_id)
                if occ.settled_transaction_id
                else None,
            }
        )
    return result


def mark_paid(db: Session, user: User, occurrence_id: uuid.UUID, transaction_id: uuid.UUID) -> dict:
    occ = _owned_occurrence(db, user, occurrence_id)
    transaction = db.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    if transaction.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Transaction does not belong to you")
    if transaction.type != TransactionType.EXPENSE.value:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Bill payment must be an expense transaction"
        )
    if transaction.status != TransactionStatus.POSTED.value:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Bill payment must be a posted transaction"
        )

    occ.status = OccurrenceStatus.PAID.value
    occ.settled_transaction_id = transaction.id
    occ.paid_at = datetime.now(UTC)
    bill = _owned(db, user, occ.bill_id)
    _refresh_next_due(db, bill, date.today())
    db.commit()
    return _occurrence_out(occ)


def skip(db: Session, user: User, occurrence_id: uuid.UUID) -> dict:
    occ = _owned_occurrence(db, user, occurrence_id)
    occ.status = OccurrenceStatus.SKIPPED.value
    bill = _owned(db, user, occ.bill_id)
    _refresh_next_due(db, bill, date.today())
    db.commit()
    return _occurrence_out(occ)


def _occurrence_out(occ: BillOccurrence) -> dict:
    return {
        "id": str(occ.id),
        "due_date": occ.due_date.isoformat(),
        "amount_minor": occ.amount_minor,
        "status": effective_status(occ, date.today()),
        "paid_at": occ.paid_at.isoformat() if occ.paid_at else None,
        "settled_transaction_id": str(occ.settled_transaction_id)
        if occ.settled_transaction_id
        else None,
    }
