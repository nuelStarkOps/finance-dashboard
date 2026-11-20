"""Category schemas."""

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: str
    icon: str | None
    color: str | None
    is_system: bool
    status: str


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    type: Literal["INCOME", "EXPENSE"]
    icon: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=20)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    icon: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=20)
