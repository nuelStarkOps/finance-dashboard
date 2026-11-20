"""Transaction and ledger entry schemas."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.category import CategoryOut

TransactionTypeLiteral = Literal["INCOME", "EXPENSE", "TRANSFER"]


class LedgerEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    amount_minor: int
    created_at: datetime


class TransactionCreate(BaseModel):
    """Create/edit payload. Type-specific fields are cross-validated here; the
    service performs ownership/currency/account checks against the database."""

    type: TransactionTypeLiteral
    amount_minor: int = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    category_id: uuid.UUID | None = None
    account_id: uuid.UUID | None = None
    source_account_id: uuid.UUID | None = None
    destination_account_id: uuid.UUID | None = None
    description: str = Field(min_length=1, max_length=255)
    transaction_date: date
    notes: str | None = Field(default=None)

    @model_validator(mode="after")
    def _validate_type_fields(self) -> "TransactionCreate":
        if self.type == "TRANSFER":
            if self.source_account_id is None or self.destination_account_id is None:
                raise ValueError("Transfers require source_account_id and destination_account_id")
            if self.category_id is not None or self.account_id is not None:
                raise ValueError("Transfers must not set category_id or account_id")
        else:
            if self.account_id is None:
                raise ValueError(f"{self.type} transactions require account_id")
            if self.category_id is None:
                raise ValueError(f"{self.type} transactions require category_id")
            if self.source_account_id is not None or self.destination_account_id is not None:
                raise ValueError(f"{self.type} transactions must not set transfer accounts")
        return self


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    amount_minor: int
    currency_code: str
    category: CategoryOut | None
    description: str
    transaction_date: date
    notes: str | None
    status: str
    idempotency_key: str | None
    voided_at: datetime | None
    created_at: datetime
    updated_at: datetime
    ledger_entries: list[LedgerEntryOut]
