"""Recurring bill endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.bill import BillCreate, BillOut, BillUpdate, MarkPaidRequest
from app.services import bills as bills_service

router = APIRouter(tags=["bills"])


@router.post("/bills")
def create_bill(
    payload: BillCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    bill = bills_service.create_bill(db, user, payload)
    return ok(BillOut.model_validate(bill).model_dump(mode="json"))


@router.get("/bills")
def list_bills(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    bills = bills_service.list_bills(db, user)
    return ok([BillOut.model_validate(b).model_dump(mode="json") for b in bills])


@router.get("/bills/{bill_id}")
def get_bill(
    bill_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    bill = bills_service.get_bill(db, user, bill_id)
    return ok(BillOut.model_validate(bill).model_dump(mode="json"))


@router.patch("/bills/{bill_id}")
def update_bill(
    bill_id: uuid.UUID,
    payload: BillUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    bill = bills_service.update_bill(db, user, bill_id, payload)
    return ok(BillOut.model_validate(bill).model_dump(mode="json"))


@router.post("/bills/{bill_id}/pause")
def pause_bill(
    bill_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    bill = bills_service.pause_bill(db, user, bill_id)
    return ok(BillOut.model_validate(bill).model_dump(mode="json"))


@router.get("/bills/{bill_id}/occurrences")
def list_occurrences(
    bill_id: uuid.UUID,
    status: str | None = Query(default=None, pattern="^(upcoming|due|overdue|paid|skipped)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(bills_service.list_occurrences(db, user, bill_id, status))


@router.post("/bill-occurrences/{occurrence_id}/mark-paid")
def mark_paid(
    occurrence_id: uuid.UUID,
    payload: MarkPaidRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(bills_service.mark_paid(db, user, occurrence_id, payload.transaction_id))


@router.post("/bill-occurrences/{occurrence_id}/skip")
def skip_occurrence(
    occurrence_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(bills_service.skip(db, user, occurrence_id))
