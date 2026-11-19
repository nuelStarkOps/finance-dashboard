"""Application settings loaded from environment variables / .env."""

from functools import lru_cache

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

    # PostgreSQL connection. Default targets the docker-compose `db` service;
    # override with `localhost` for host-based development.
    database_url: str = "postgresql+psycopg://pfos:pfos_dev_password@localhost:5432/pfos"

    # Amazon Cognito (wired up in Phase 1).
    cognito_user_pool_id: str | None = None
    cognito_client_id: str | None = None
    cognito_region: str = "eu-west-1"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
