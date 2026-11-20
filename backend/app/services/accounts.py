"""Account service — CRUD, archiving, balance and account activity."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.models.account import Account
from app.models.enums import AccountStatus
from app.models.transaction import LedgerEntry, Transaction
from app.models.user import User
from app.schemas.account import AccountCreate, AccountUpdate
from app.services.ledger import compute_balance


def _owned_account(db: Session, user: User, account_id: uuid.UUID) -> Account:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
    if account.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account does not belong to you")
    return account


def create_account(db: Session, user: User, payload: AccountCreate) -> Account:
    account = Account(
        user_id=user.id,
        name=payload.name,
        account_type=payload.account_type,
        currency_code=payload.currency_code,
        opening_balance_minor=payload.opening_balance_minor,
        opening_date=payload.opening_date,
        description=payload.description,
        status=AccountStatus.ACTIVE.value,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def list_accounts(db: Session, user: User) -> list[Account]:
    return (
        db.query(Account)
        .filter(Account.user_id == user.id)
        .order_by(Account.created_at.desc())
        .all()
    )


def get_account(db: Session, user: User, account_id: uuid.UUID) -> Account:
    return _owned_account(db, user, account_id)


def update_account(
    db: Session, user: User, account_id: uuid.UUID, payload: AccountUpdate
) -> Account:
    account = _owned_account(db, user, account_id)
    if payload.name is not None:
        account.name = payload.name
    if payload.account_type is not None:
        account.account_type = payload.account_type
    if payload.opening_balance_minor is not None:
        account.opening_balance_minor = payload.opening_balance_minor
    if payload.opening_date is not None:
        account.opening_date = payload.opening_date
    if payload.description is not None:
        account.description = payload.description
    db.commit()
    db.refresh(account)
    return account


def archive_account(db: Session, user: User, account_id: uuid.UUID) -> Account:
    account = _owned_account(db, user, account_id)
    account.status = AccountStatus.ARCHIVED.value
    db.commit()
    db.refresh(account)
    return account


def get_balance(db: Session, user: User, account_id: uuid.UUID) -> tuple[Account, int, int]:
    """Return ``(account, posted_minor, balance_minor)``."""
    account = _owned_account(db, user, account_id)
    posted, balance = compute_balance(db, account)
    return account, posted, balance


def list_account_transactions(
    db: Session, user: User, account_id: uuid.UUID, page: int, limit: int
) -> tuple[list[Transaction], int]:
    _owned_account(db, user, account_id)
    base = (
        db.query(Transaction)
        .join(LedgerEntry, LedgerEntry.transaction_id == Transaction.id)
        .filter(LedgerEntry.account_id == account_id)
    )
    total = base.count()
    items = (
        base.options(
            selectinload(Transaction.category),
            selectinload(Transaction.ledger_entries),
        )
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return items, total
