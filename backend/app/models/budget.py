"""Budget and budget-item models."""

import uuid
from datetime import date

from sqlalchemy import (
    CHAR,
    BigInteger,
    Date,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import BudgetStatus


class Budget(Base, TimestampMixin):
    """A spending budget (overall, category-based, or both)."""

    __tablename__ = "budgets"
    __table_args__ = (Index("ix_budgets_user_period", "user_id", "start_date", "end_date"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_limit_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BudgetStatus.ACTIVE.value
    )

    items: Mapped[list["BudgetItem"]] = relationship(
        back_populates="budget", cascade="all, delete-orphan"
    )


class BudgetItem(Base):
    """A per-category limit within a budget."""

    __tablename__ = "budget_items"
    __table_args__ = (
        UniqueConstraint("budget_id", "category_id", name="uq_budget_items_budget_category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    budget_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("categories.id"), nullable=False
    )
    limit_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)

    budget: Mapped["Budget"] = relationship(back_populates="items")
    category: Mapped["Category"] = relationship()  # noqa: F821
