"""Amazon Cognito provider.

Verifies Cognito access/id tokens against the pool's JWKS, checking issuer,
audience, expiry and signature. Enable by setting ``AUTH_PROVIDER=cognito`` and
providing ``COGNITO_USER_POOL_ID`` / ``COGNITO_CLIENT_ID``.
"""

import jwt
from jwt import PyJWKClient

from app.core.config import settings


class CognitoAuthProvider:
    """Validates Cognito-issued JWTs via the pool's JSON Web Key Set."""

    def __init__(self) -> None:
        self._jwks = PyJWKClient(settings.cognito_jwks_url_derived, cache_keys=True)
        self.issuer = settings.cognito_issuer_url
        self.audience = settings.cognito_client_id

    def validate(self, token: str) -> dict:
        signing_key = self._jwks.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self.audience,
            issuer=self.issuer,
        )
        # Access tokens use `token_use=access`, id tokens `token_use=id`.
        if claims.get("token_use") not in (None, "access", "id"):
            raise jwt.InvalidTokenError("Unsupported token_use claim")
        return claims
