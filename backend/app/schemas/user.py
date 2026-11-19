"""User schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str
    country_code: str
    status: str
    created_at: datetime


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    country_code: str | None = Field(
        default=None, min_length=2, max_length=2, pattern=r"^[A-Z]{2}$"
    )
