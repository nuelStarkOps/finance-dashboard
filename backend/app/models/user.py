"""User identity and preference models."""

import uuid

from sqlalchemy import CHAR, Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import Theme, UserStatus


class User(Base, TimestampMixin):
    """Application user mapped to an identity-provider subject (Cognito/dev)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    auth_subject: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=UserStatus.ACTIVE.value)

    preferences: Mapped["UserPreference"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserPreference(Base):
    """Per-user preferences with Nigerian defaults per the product spec."""

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    preferred_currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="NGN")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Africa/Lagos")
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en-NG")
    theme: Mapped[str] = mapped_column(String(10), nullable=False, default=Theme.SYSTEM.value)
    date_format: Mapped[str] = mapped_column(String(20), nullable=False, default="DD/MM/YYYY")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship(back_populates="preferences")
