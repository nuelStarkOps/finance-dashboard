"""User preference schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PreferencesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    preferred_currency: str
    timezone: str
    locale: str
    theme: str
    date_format: str
    onboarding_completed: bool


class PreferencesUpdate(BaseModel):
    preferred_currency: str | None = Field(
        default=None, min_length=3, max_length=3, pattern=r"^[A-Z]{3}$"
    )
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    locale: str | None = Field(default=None, min_length=1, max_length=16)
    theme: Literal["system", "light", "dark"] | None = None
    date_format: str | None = Field(default=None, min_length=1, max_length=20)
