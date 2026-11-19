"""ORM models.

Models are added per module in later phases (accounts, transactions, ledger,
budgets, savings, bills, etc.). Importing them here registers them with the
SQLAlchemy metadata so Alembic autogenerate can see them.
"""

from app.db.base import Base  # noqa: F401  (re-export for Alembic)
