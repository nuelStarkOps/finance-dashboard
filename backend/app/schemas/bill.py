"""Recurring bill schemas."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryOut

BillFrequency = Literal["WEEKLY", "MONTHLY", "QUARTERLY", "ANNUALLY", "CUSTOM"]


class BillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount_minor: int = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    category_id: uuid.UUID | None = None
    frequency: BillFrequency = "MONTHLY"
    interval_value: int = Field(default=1, ge=1)
    next_due_date: date
    reminder_days: int = Field(default=0, ge=0)


class BillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    amount_minor: int | None = Field(default=None, gt=0)
    category_id: uuid.UUID | None = None
    reminder_days: int | None = Field(default=None, ge=0)


class BillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    amount_minor: int
    currency_code: str
    category: CategoryOut | None
    frequency: str
    interval_value: int
    next_due_date: date
    reminder_days: int
    status: str
    created_at: datetime
    updated_at: datetime


class MarkPaidRequest(BaseModel):
    transaction_id: uuid.UUID
