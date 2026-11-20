"""Account schemas (Phase 1 + Phase 2)."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AccountType = Literal["CASH", "CURRENT", "SAVINGS", "OTHER"]


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    account_type: AccountType = "CURRENT"
    currency_code: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    opening_balance_minor: int = Field(ge=0)
    opening_date: date
    description: str | None = Field(default=None, max_length=2000)


class AccountUpdate(BaseModel):
    """Editable fields. Currency is immutable once an account exists."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    account_type: AccountType | None = None
    opening_balance_minor: int | None = Field(default=None, ge=0)
    opening_date: date | None = None
    description: str | None = Field(default=None, max_length=2000)


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    account_type: str
    currency_code: str
    opening_balance_minor: int
    opening_date: date
    description: str | None
    status: str
    created_at: datetime


class AccountBalanceOut(BaseModel):
    account_id: uuid.UUID
    currency_code: str
    opening_balance_minor: int
    posted_minor: int
    balance_minor: int
