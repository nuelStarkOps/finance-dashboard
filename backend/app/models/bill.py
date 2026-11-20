"""Recurring bill and occurrence models."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CHAR,
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import BillFrequency, BillStatus, OccurrenceStatus


class RecurringBill(Base, TimestampMixin):
    """A scheduled obligation. Occurrences are generated ahead of time."""

    __tablename__ = "recurring_bills"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("categories.id"), nullable=True
    )
    frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BillFrequency.MONTHLY.value
    )
    interval_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    reminder_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=BillStatus.ACTIVE.value)

    occurrences: Mapped[list["BillOccurrence"]] = relationship(
        back_populates="bill", cascade="all, delete-orphan"
    )
    category: Mapped["Category | None"] = relationship()  # noqa: F821


class BillOccurrence(Base):
    """A single expected bill due date."""

    __tablename__ = "bill_occurrences"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    bill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("recurring_bills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=OccurrenceStatus.PENDING.value
    )
    settled_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("transactions.id"), nullable=True
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    bill: Mapped["RecurringBill"] = relationship(back_populates="occurrences")
