"""Local development identity provider.

Signs and verifies RS256 JWTs with an in-process key. This exists ONLY so the
full authentication flow can be exercised locally without an external service
(the spec's "Development Cognito / Auth Test"). It is never used in production.

The key is regenerated on process start, so dev tokens do not survive restarts
(single-worker uvicorn only).
"""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import settings

# Deterministic subject per email so a user maps to the same local row across
# dev restarts, without using the email as the subject itself.
_DEV_SUBJECT_NAMESPACE = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")


def dev_subject_for(email: str) -> str:
    """Return a stable, non-email subject for a dev identity."""
    return str(uuid.uuid5(_DEV_SUBJECT_NAMESPACE, f"pfos-dev:{email.strip().lower()}"))


class DevAuthProvider:
    """Issues and validates local dev JWTs (RS256)."""

    def __init__(self) -> None:
        self._private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.issuer = settings.dev_issuer
        self.audience = settings.dev_audience

    def issue_token(
        self,
        *,
        subject: str,
        email: str,
        name: str,
        token_use: str = "access",
        expires_delta: timedelta | None = None,
    ) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        now = datetime.now(UTC)
        payload = {
            "sub": subject,
            "email": email,
            "name": name,
            "iss": self.issuer,
            "aud": self.audience,
            "iat": now,
            "exp": now + expires_delta,
            "token_use": token_use,
        }
        return jwt.encode(payload, self._private_key, algorithm="RS256")

    def validate(self, token: str) -> dict:
        return jwt.decode(
            token,
            self._private_key.public_key(),
            algorithms=["RS256"],
            audience=self.audience,
            issuer=self.issuer,
        )
