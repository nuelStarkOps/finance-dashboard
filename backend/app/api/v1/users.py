"""Current-user profile, preferences and onboarding endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.account import Account
from app.models.enums import AccountStatus, UserStatus
from app.models.user import User, UserPreference
from app.schemas.account import AccountOut
from app.schemas.onboarding import OnboardingRequest, OnboardingResult
from app.schemas.preferences import PreferencesOut, PreferencesUpdate
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _get_preferences(db: Session, user: User) -> UserPreference:
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    if prefs is None:
        prefs = UserPreference(user_id=user.id)
        db.add(prefs)
        db.flush()
    return prefs


@router.get("/me")
def get_me(user: User = Depends(get_current_user)) -> dict:
    return ok(UserOut.model_validate(user).model_dump(mode="json"))


@router.patch("/me")
def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.country_code is not None:
        user.country_code = payload.country_code
    db.commit()
    db.refresh(user)
    return ok(UserOut.model_validate(user).model_dump(mode="json"))


@router.get("/me/preferences")
def get_preferences(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    prefs = _get_preferences(db, user)
    return ok(PreferencesOut.model_validate(prefs).model_dump(mode="json"))


@router.patch("/me/preferences")
def update_preferences(
    payload: PreferencesUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    prefs = _get_preferences(db, user)
    for field in (
        "preferred_currency",
        "timezone",
        "locale",
        "theme",
        "date_format",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(prefs, field, value)
    db.commit()
    db.refresh(prefs)
    return ok(PreferencesOut.model_validate(prefs).model_dump(mode="json"))


@router.post("/me/onboarding")
def complete_onboarding(
    payload: OnboardingRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Apply profile + preferences and create the first account."""
    user.display_name = payload.display_name
    user.country_code = payload.country_code

    prefs = _get_preferences(db, user)
    prefs.preferred_currency = payload.preferred_currency
    prefs.timezone = payload.timezone
    prefs.locale = payload.locale
    prefs.onboarding_completed = True

    account = Account(
        user_id=user.id,
        name=payload.account.name,
        account_type=payload.account.account_type,
        currency_code=payload.account.currency_code,
        opening_balance_minor=payload.account.opening_balance_minor,
        opening_date=payload.account.opening_date,
        description=payload.account.description,
        status=AccountStatus.ACTIVE.value,
    )
    db.add(account)
    db.commit()
    db.refresh(user)
    db.refresh(prefs)
    db.refresh(account)

    result = OnboardingResult(
        user=UserOut.model_validate(user),
        preferences=PreferencesOut.model_validate(prefs),
        account=AccountOut.model_validate(account),
    )
    return ok(result.model_dump(mode="json"))


@router.post("/me/export")
def export_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Basic JSON export of the user's own records (full export in Phase 6)."""
    prefs = _get_preferences(db, user)
    accounts = db.query(Account).filter(Account.user_id == user.id).all()
    data = {
        "user": UserOut.model_validate(user).model_dump(mode="json"),
        "preferences": PreferencesOut.model_validate(prefs).model_dump(mode="json"),
        "accounts": [AccountOut.model_validate(a).model_dump(mode="json") for a in accounts],
    }
    return ok(data)


@router.delete("/me", status_code=204)
def delete_me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Soft-delete the account (full erasure + retention policy in Phase 7)."""
    user.status = UserStatus.DELETED.value
    db.commit()
