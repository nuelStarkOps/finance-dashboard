"""Local development identity provider endpoints.

Mounted only when ``AUTH_PROVIDER=dev`` and ``DEV_AUTH_ENABLED=true``. These
simulate register / login / verification / password recovery so the complete
flow can be exercised without Cognito or an email service.

DEV-ONLY: all identity state is held in process memory and never persisted.
Passwords are lightly hashed (SHA-256 + salt) purely to make the local login
flow realistic — this is NOT production password handling, which is delegated
to Amazon Cognito.
"""

import hashlib
import secrets
import threading
from datetime import timedelta

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.auth.deps import get_dev_provider, provision_user
from app.auth.dev import DevAuthProvider, dev_subject_for
from app.core.config import settings
from app.db.session import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserOut

router = APIRouter(prefix="/dev-auth", tags=["dev-auth"])

_store_lock = threading.Lock()
_dev_users: dict[str, dict] = {}


def _hash(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _issue_tokens(provider: DevAuthProvider, *, email: str, name: str) -> tuple[str, str, int]:
    subject = dev_subject_for(email)
    access = provider.issue_token(subject=subject, email=email, name=name, token_use="access")
    refresh = provider.issue_token(
        subject=subject,
        email=email,
        name=name,
        token_use="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    return access, refresh, settings.access_token_expire_minutes * 60


def _token_response(provider: DevAuthProvider, email: str, name: str, db: Session) -> dict:
    access, refresh, expires = _issue_tokens(provider, email=email, name=name)
    user = provision_user(db, {"sub": dev_subject_for(email), "email": email, "name": name})
    payload = TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=expires,
        user=UserOut.model_validate(user),
    )
    return ok(payload.model_dump(mode="json"))


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    provider = get_dev_provider()
    email = payload.email.lower()
    with _store_lock:
        if email in _dev_users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )
        salt = secrets.token_hex(16)
        _dev_users[email] = {
            "password_hash": _hash(payload.password, salt),
            "salt": salt,
            "name": payload.display_name,
            "verified": True,  # dev: email verification is automatic
            "reset_code": None,
        }
    return _token_response(provider, email=email, name=payload.display_name, db=db)


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    provider = get_dev_provider()
    email = payload.email.lower()
    with _store_lock:
        entry = _dev_users.get(email)
        if entry is None or entry["password_hash"] != _hash(payload.password, entry["salt"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        name = entry["name"]
    return _token_response(provider, email=email, name=name, db=db)


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest) -> dict:
    email = payload.email.lower()
    with _store_lock:
        entry = _dev_users.get(email)
        if entry is None:
            # Do not reveal whether the email exists.
            return ok(
                ForgotPasswordResponse(
                    success=True,
                    reset_code="",
                    message="If the email exists, a reset code was generated.",
                ).model_dump(mode="json")
            )
        code = secrets.token_hex(3)  # short dev code
        entry["reset_code"] = code
    return ok(
        ForgotPasswordResponse(
            success=True,
            reset_code=code,
            message="Dev reset code returned (no email service configured).",
        ).model_dump(mode="json")
    )


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest) -> dict:
    email = payload.email.lower()
    with _store_lock:
        entry = _dev_users.get(email)
        if entry is None or entry.get("reset_code") != payload.reset_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset code",
            )
        salt = secrets.token_hex(16)
        entry["salt"] = salt
        entry["password_hash"] = _hash(payload.new_password, salt)
        entry["reset_code"] = None
    return ok({"message": "Password reset successfully."})


@router.post("/refresh")
def refresh(payload: RefreshRequest) -> dict:
    provider = get_dev_provider()
    try:
        claims = provider.validate(payload.refresh_token)
    except pyjwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc
    if claims.get("token_use") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")
    access = provider.issue_token(
        subject=claims["sub"],
        email=claims.get("email", ""),
        name=claims.get("name", ""),
        token_use="access",
    )
    return ok(
        RefreshResponse(
            access_token=access,
            expires_in=settings.access_token_expire_minutes * 60,
        ).model_dump(mode="json")
    )
