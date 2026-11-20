"""Transaction service — income, expenses and transfers.

Transactions are ledger-centric: a posted transaction produces signed ledger
entries (income +, expense −, transfer source −/destination +). Editing voids the
original and posts a corrected transaction; voiding marks the original VOIDED
and excludes it from balances, preserving the audit trail.
"""

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.account import Account
from app.models.category import Category
from app.models.enums import AccountStatus, CategoryStatus, TransactionStatus
from app.models.transaction import LedgerEntry, Transaction
from app.models.user import User
from app.schemas.transaction import TransactionCreate
from app.services import ledger


def _load(db: Session, transaction_id: uuid.UUID) -> Transaction | None:
    return (
        db.query(Transaction)
        .options(
            selectinload(Transaction.category),
            selectinload(Transaction.ledger_entries),
        )
        .filter(Transaction.id == transaction_id)
        .one_or_none()
    )


def _owned(db: Session, user: User, transaction_id: uuid.UUID) -> Transaction:
    transaction = _load(db, transaction_id)
    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    if transaction.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Transaction does not belong to you")
    return transaction


def _existing_by_idempotency(
    db: Session, user: User, idempotency_key: str | None
) -> Transaction | None:
    if not idempotency_key:
        return None
    return (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user.id,
            Transaction.idempotency_key == idempotency_key,
        )
        .first()
    )


def _check_account(db: Session, user: User, account: Account | None, currency: str) -> None:
    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
    if account.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account does not belong to you")
    if account.status != AccountStatus.ACTIVE.value:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Archived accounts cannot receive transactions"
        )
    if account.currency_code != currency:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Transaction currency must match the account currency"
        )


def _check_category(db: Session, user: User, payload: TransactionCreate) -> Category:
    category = db.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    if category.status != CategoryStatus.ACTIVE.value:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Category is archived")
    if category.type != payload.type:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Category type does not match transaction type"
        )
    if category.user_id is not None and category.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Category does not belong to you")
    return category


def _resolve_entries(
    db: Session, user: User, payload: TransactionCreate
) -> tuple[list[tuple[uuid.UUID, int]], Category | None]:
    """Validate accounts/category and return ``(entries, category)``."""
    category: Category | None = None
    if payload.type == "TRANSFER":
        source = db.get(Account, payload.source_account_id)
        destination = db.get(Account, payload.destination_account_id)
        _check_account(db, user, source, payload.currency_code)
        _check_account(db, user, destination, payload.currency_code)
        if source.id == destination.id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Source and destination accounts must differ",
            )
        if source.currency_code != destination.currency_code:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Transfers require accounts with the same currency",
            )
        entries = [(source.id, -payload.amount_minor), (destination.id, payload.amount_minor)]
    else:
        account = db.get(Account, payload.account_id)
        _check_account(db, user, account, payload.currency_code)
        category = _check_category(db, user, payload)
        sign = 1 if payload.type == "INCOME" else -1
        entries = [(account.id, sign * payload.amount_minor)]
    return entries, category


def _build(
    db: Session, user: User, payload: TransactionCreate, idempotency_key: str | None
) -> Transaction:
    entries, category = _resolve_entries(db, user, payload)
    transaction = Transaction(
        user_id=user.id,
        type=payload.type,
        amount_minor=payload.amount_minor,
        currency_code=payload.currency_code,
        category_id=category.id if category else None,
        description=payload.description,
        transaction_date=payload.transaction_date,
        notes=payload.notes,
        status=TransactionStatus.POSTED.value,
        idempotency_key=idempotency_key,
    )
    db.add(transaction)
    db.flush()
    ledger.add_entries(db, transaction=transaction, entries=entries)
    return transaction


def create_transaction(
    db: Session, user: User, payload: TransactionCreate, idempotency_key: str | None
) -> Transaction:
    existing = _existing_by_idempotency(db, user, idempotency_key)
    if existing is not None:
        return _load(db, existing.id)
    transaction = _build(db, user, payload, idempotency_key)
    db.commit()
    return _load(db, transaction.id)


def get_transaction(db: Session, user: User, transaction_id: uuid.UUID) -> Transaction:
    return _owned(db, user, transaction_id)


def list_transactions(
    db: Session,
    user: User,
    *,
    type_filter: str | None = None,
    category_id: uuid.UUID | None = None,
    account_id: uuid.UUID | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    query: str | None = None,
    sort: str = "date_desc",
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Transaction], int]:
    q = db.query(Transaction).filter(Transaction.user_id == user.id)
    if type_filter:
        q = q.filter(Transaction.type == type_filter)
    if category_id:
        q = q.filter(Transaction.category_id == category_id)
    if from_date:
        q = q.filter(Transaction.transaction_date >= from_date)
    if to_date:
        q = q.filter(Transaction.transaction_date <= to_date)
    if query:
        pattern = f"%{query}%"
        q = q.filter(
            or_(
                Transaction.description.ilike(pattern),
                Transaction.notes.ilike(pattern),
            )
        )
    if account_id:
        q = q.join(LedgerEntry, LedgerEntry.transaction_id == Transaction.id).filter(
            LedgerEntry.account_id == account_id
        )

    total = q.count()

    if sort == "amount_desc":
        order = Transaction.amount_minor.desc()
    elif sort == "amount_asc":
        order = Transaction.amount_minor.asc()
    elif sort == "date_asc":
        order = Transaction.transaction_date.asc()
    else:
        order = Transaction.transaction_date.desc()

    items = (
        q.options(
            selectinload(Transaction.category),
            selectinload(Transaction.ledger_entries),
        )
        .order_by(order, Transaction.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return items, total


def void_transaction(db: Session, user: User, transaction_id: uuid.UUID) -> Transaction:
    transaction = _owned(db, user, transaction_id)
    if transaction.status != TransactionStatus.VOIDED.value:
        transaction.status = TransactionStatus.VOIDED.value
        transaction.voided_at = datetime.now(UTC)
        db.commit()
    return _load(db, transaction.id)


def edit_transaction(
    db: Session,
    user: User,
    transaction_id: uuid.UUID,
    payload: TransactionCreate,
    idempotency_key: str | None,
) -> Transaction:
    existing = _existing_by_idempotency(db, user, idempotency_key)
    if existing is not None:
        return _load(db, existing.id)

    original = _owned(db, user, transaction_id)
    if original.status != TransactionStatus.VOIDED.value:
        original.status = TransactionStatus.VOIDED.value
        original.voided_at = datetime.now(UTC)

    corrected = _build(db, user, payload, idempotency_key)
    db.commit()
    return _load(db, corrected.id)
