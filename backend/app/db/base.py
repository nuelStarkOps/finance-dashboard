"""Declarative base and shared column mixins for all ORM models."""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class TimestampMixin:
    """Adds ``created_at`` / ``updated_at`` TIMESTAMPTZ columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
