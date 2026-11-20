"""Account endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.account import AccountBalanceOut, AccountCreate, AccountOut, AccountUpdate
from app.schemas.transaction import TransactionOut
from app.services import accounts as accounts_service

router = APIRouter(tags=["accounts"])


@router.post("/accounts")
def create_account(
    payload: AccountCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    account = accounts_service.create_account(db, user, payload)
    return ok(AccountOut.model_validate(account).model_dump(mode="json"))


@router.get("/accounts")
def list_accounts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    accounts = accounts_service.list_accounts(db, user)
    return ok([AccountOut.model_validate(a).model_dump(mode="json") for a in accounts])


@router.get("/accounts/{account_id}")
def get_account(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    account = accounts_service.get_account(db, user, account_id)
    return ok(AccountOut.model_validate(account).model_dump(mode="json"))


@router.patch("/accounts/{account_id}")
def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    account = accounts_service.update_account(db, user, account_id, payload)
    return ok(AccountOut.model_validate(account).model_dump(mode="json"))


@router.post("/accounts/{account_id}/archive")
def archive_account(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    account = accounts_service.archive_account(db, user, account_id)
    return ok(AccountOut.model_validate(account).model_dump(mode="json"))


@router.get("/accounts/{account_id}/balance")
def get_balance(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    account, posted, balance = accounts_service.get_balance(db, user, account_id)
    payload = AccountBalanceOut(
        account_id=account.id,
        currency_code=account.currency_code,
        opening_balance_minor=account.opening_balance_minor,
        posted_minor=posted,
        balance_minor=balance,
    )
    return ok(payload.model_dump(mode="json"))


@router.get("/accounts/{account_id}/transactions")
def list_account_transactions(
    account_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items, total = accounts_service.list_account_transactions(db, user, account_id, page, limit)
    data = [TransactionOut.model_validate(t).model_dump(mode="json") for t in items]
    return ok(data, meta={"page": page, "limit": limit, "total": total})
