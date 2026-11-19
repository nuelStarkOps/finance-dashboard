"""Auth provider abstraction.

A provider validates a Bearer token and returns its decoded claims. The rest of
the application only depends on this interface, so a new OIDC provider can be
introduced without touching resource code.
"""

from typing import Any, Protocol

#: Decoded JWT claims (subset used by the application).
TokenClaims = dict[str, Any]


class AuthProvider(Protocol):
    """Validates JWTs issued by an identity provider."""

    def validate(self, token: str) -> TokenClaims:
        """Return the decoded claims, raising ``jwt.PyJWTError`` on failure."""
        ...
