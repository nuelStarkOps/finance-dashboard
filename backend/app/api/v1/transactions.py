"""Transaction endpoints — income, expense, transfer, and ledger."""

import csv
import io
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transaction import LedgerEntryOut, TransactionCreate, TransactionOut
from app.services import transactions as transactions_service

router = APIRouter(tags=["transactions"])


@router.post("/transactions")
def create_transaction(
    payload: TransactionCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    transaction = transactions_service.create_transaction(db, user, payload, idempotency_key)
    return ok(TransactionOut.model_validate(transaction).model_dump(mode="json"))


@router.get("/transactions")
def list_transactions(
    type: str | None = Query(default=None, pattern="^(INCOME|EXPENSE|TRANSFER)$"),
    category_id: uuid.UUID | None = Query(default=None),
    account_id: uuid.UUID | None = Query(default=None),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    q: str | None = Query(default=None),
    sort: str = Query(default="date_desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items, total = transactions_service.list_transactions(
        db,
        user,
        type_filter=type,
        category_id=category_id,
        account_id=account_id,
        from_date=from_date.isoformat() if from_date else None,
        to_date=to_date.isoformat() if to_date else None,
        query=q,
        sort=sort,
        page=page,
        limit=limit,
    )
    data = [TransactionOut.model_validate(t).model_dump(mode="json") for t in items]
    return ok(data, meta={"page": page, "limit": limit, "total": total})


@router.get("/transactions/{transaction_id}")
def get_transaction(
    transaction_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    transaction = transactions_service.get_transaction(db, user, transaction_id)
    return ok(TransactionOut.model_validate(transaction).model_dump(mode="json"))


@router.patch("/transactions/{transaction_id}")
def edit_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    transaction = transactions_service.edit_transaction(
        db, user, transaction_id, payload, idempotency_key
    )
    return ok(TransactionOut.model_validate(transaction).model_dump(mode="json"))


@router.post("/transactions/{transaction_id}/void")
def void_transaction(
    transaction_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    transaction = transactions_service.void_transaction(db, user, transaction_id)
    return ok(TransactionOut.model_validate(transaction).model_dump(mode="json"))


@router.get("/transactions/{transaction_id}/ledger")
def get_transaction_ledger(
    transaction_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    transaction = transactions_service.get_transaction(db, user, transaction_id)
    entries = [
        LedgerEntryOut.model_validate(e).model_dump(mode="json") for e in transaction.ledger_entries
    ]
    return ok(entries)


@router.get("/transactions/export")
def export_transactions(
    type: str | None = Query(default=None, pattern="^(INCOME|EXPENSE|TRANSFER)$"),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Export the current filter to CSV (full export workflows arrive in Phase 6)."""
    items, _ = transactions_service.list_transactions(
        db,
        user,
        type_filter=type,
        from_date=from_date.isoformat() if from_date else None,
        to_date=to_date.isoformat() if to_date else None,
        page=1,
        limit=10_000,
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "type",
            "amount_minor",
            "currency",
            "category",
            "description",
            "date",
            "notes",
            "status",
            "ledger",
        ]
    )
    for t in items:
        ledger = ";".join(f"{e.account_id}:{e.amount_minor}" for e in t.ledger_entries)
        writer.writerow(
            [
                t.id,
                t.type,
                t.amount_minor,
                t.currency_code,
                t.category.name if t.category else "",
                t.description,
                t.transaction_date.isoformat(),
                t.notes or "",
                t.status,
                ledger,
            ]
        )

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'},
    )
