"""Ledger service — authoritative account movement and balance calculation.

Posted ledger entries are immutable. A transaction posts one entry for
income/expense (signed +/−) or two entries for a transfer (source −, destination
+). Balances are always derived from the ledger, never stored.
"""

import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import TransactionStatus
from app.models.transaction import LedgerEntry, Transaction


def add_entries(
    db: Session,
    *,
    transaction: Transaction,
    entries: list[tuple[uuid.UUID, int]],
) -> None:
    """Add ledger entries for a transaction. Entries are ``(account_id, signed_amount)``.

    The caller is responsible for committing; this keeps the transaction and its
    entries in a single atomic database transaction.
    """
    for account_id, amount_minor in entries:
        db.add(
            LedgerEntry(
                user_id=transaction.user_id,
                transaction_id=transaction.id,
                account_id=account_id,
                amount_minor=amount_minor,
            )
        )


def posted_total(db: Session, account_id: uuid.UUID) -> int:
    """Sum of ledger entries for an account, excluding voided transactions."""
    return int(
        db.query(func.coalesce(func.sum(LedgerEntry.amount_minor), 0))
        .join(Transaction, Transaction.id == LedgerEntry.transaction_id)
        .filter(
            LedgerEntry.account_id == account_id,
            Transaction.status == TransactionStatus.POSTED.value,
        )
        .scalar()
        or 0
    )


def compute_balance(db: Session, account: Account) -> tuple[int, int]:
    """Return ``(posted_minor, balance_minor)`` for an account."""
    posted = posted_total(db, account.id)
    return posted, account.opening_balance_minor + posted
