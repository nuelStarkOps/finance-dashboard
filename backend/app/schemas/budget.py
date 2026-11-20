"""Budget schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.category import CategoryOut


class BudgetItemIn(BaseModel):
    category_id: uuid.UUID
    limit_minor: int = Field(ge=0)


class BudgetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    currency_code: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    start_date: date
    end_date: date
    total_limit_minor: int | None = Field(default=None, ge=0)
    items: list[BudgetItemIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate(self) -> "BudgetCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        ids = [i.category_id for i in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate category in budget items")
        return self


class BudgetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    total_limit_minor: int | None = Field(default=None, ge=0)


class BudgetItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    limit_minor: int
    category: CategoryOut


class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    currency_code: str
    start_date: date
    end_date: date
    total_limit_minor: int | None
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[BudgetItemOut]
