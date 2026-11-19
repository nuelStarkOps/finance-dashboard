"""Onboarding schemas."""

from pydantic import BaseModel, Field

from app.schemas.account import AccountCreate, AccountOut
from app.schemas.preferences import PreferencesOut
from app.schemas.user import UserOut


class OnboardingRequest(BaseModel):
    """Payload for completing onboarding (stages 1–2 & 4)."""

    display_name: str = Field(min_length=1, max_length=120)
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    preferred_currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    timezone: str = Field(min_length=1, max_length=64)
    locale: str = Field(min_length=1, max_length=16)
    account: AccountCreate


class OnboardingResult(BaseModel):
    user: UserOut
    preferences: PreferencesOut
    account: AccountOut
