"""Provider selection and the FastAPI dependency for authenticated users."""

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.base import AuthProvider, TokenClaims
from app.auth.cognito import CognitoAuthProvider
from app.auth.dev import DevAuthProvider
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserPreference

bearer_scheme = HTTPBearer(auto_error=False)

_provider: AuthProvider | None = None


def get_auth_provider() -> AuthProvider:
    """Return the configured auth provider as a process-wide singleton."""
    global _provider
    if _provider is None:
        _provider = (
            CognitoAuthProvider() if settings.auth_provider == "cognito" else DevAuthProvider()
        )
    return _provider


def get_dev_provider() -> DevAuthProvider:
    """Return the dev provider for the local dev-auth endpoints."""
    provider = get_auth_provider()
    if not isinstance(provider, DevAuthProvider):
        raise RuntimeError("Dev auth provider is not active")
    return provider


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate the Bearer token and return (or provision) the local user.

    Every user-owned resource must go through this dependency. It never trusts a
    user id supplied by the client.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        claims = get_auth_provider().validate(credentials.credentials)
    except pyjwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
    return provision_user(db, claims)


def provision_user(db: Session, claims: TokenClaims) -> User:
    """Create the local user row on first authenticated request, if needed."""
    subject = claims.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing a subject claim",
        )

    user = db.query(User).filter(User.auth_subject == subject).first()
    if user is None:
        email = claims.get("email") or f"{subject}@pfos.local"
        display_name = claims.get("name") or (email.split("@", 1)[0] if email else "User")
        user = User(
            auth_subject=subject,
            email=email,
            display_name=display_name[:120],
            country_code="NG",
            status="ACTIVE",
        )
        db.add(user)
        db.flush()
        db.add(
            UserPreference(
                user_id=user.id,
                preferred_currency="NGN",
                timezone="Africa/Lagos",
                locale="en-NG",
                theme="SYSTEM",
                date_format="DD/MM/YYYY",
                onboarding_completed=False,
            )
        )
        db.commit()
        db.refresh(user)
    return user
