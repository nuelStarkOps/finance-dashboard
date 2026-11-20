"""Savings goal schemas."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GoalPriority = Literal["LOW", "MEDIUM", "HIGH"]


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    currency_code: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    target_minor: int = Field(gt=0)
    target_date: date | None = None
    priority: GoalPriority = "MEDIUM"


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    target_minor: int | None = Field(default=None, gt=0)
    target_date: date | None = None
    priority: GoalPriority | None = None
    status: Literal["ACTIVE", "COMPLETED", "PAUSED"] | None = None


class ContributionCreate(BaseModel):
    amount_minor: int = Field(gt=0)
    contribution_type: Literal["CONTRIBUTION", "WITHDRAWAL", "ADJUSTMENT"] = "CONTRIBUTION"
    contribution_date: date
    notes: str | None = Field(default=None)


class ContributionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount_minor: int
    contribution_type: str
    contribution_date: date
    notes: str | None
    created_at: datetime


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    currency_code: str
    target_minor: int
    target_date: date | None
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
