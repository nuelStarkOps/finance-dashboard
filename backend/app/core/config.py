"""Application settings loaded from environment variables / .env."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration.

    Values map to uppercase environment variables (e.g. ``DATABASE_URL``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Personal Finance OS API"
    environment: str = "development"

    # Comma-separated list of allowed browser origins (the Next.js dev server).
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # PostgreSQL connection. Default targets the docker-compose `db` service;
    # override with `localhost` for host-based development.
    database_url: str = "postgresql+psycopg://pfos:pfos_dev_password@localhost:5432/pfos"

    # ------------------------------------------------------------------ #
    # Authentication (OIDC-compatible abstraction)
    # ------------------------------------------------------------------ #
    # `dev` uses a built-in local identity provider (no external service).
    # `cognito` verifies JWTs issued by an Amazon Cognito user pool.
    auth_provider: Literal["dev", "cognito"] = "dev"

    # Local development identity provider (disabled automatically for cognito).
    dev_auth_enabled: bool = True
    dev_issuer: str = "pfos-dev"
    dev_audience: str = "pfos-dev-client"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Amazon Cognito (required when auth_provider = "cognito").
    cognito_user_pool_id: str | None = None
    cognito_client_id: str | None = None
    cognito_region: str = "eu-west-1"
    # Optional overrides; derived from the values above when unset.
    cognito_issuer: str | None = None
    cognito_jwks_url: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def cognito_issuer_url(self) -> str:
        return self.cognito_issuer or (
            f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}"
        )

    @property
    def cognito_jwks_url_derived(self) -> str:
        return self.cognito_jwks or f"{self.cognito_issuer_url}/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
