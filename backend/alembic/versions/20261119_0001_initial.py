"""initial baseline (no tables yet)

Revision ID: 0001
Revises:
Create Date: 2026-11-19

The full PFOS schema (users, accounts, transactions, ledger, budgets, savings,
bills, etc.) is introduced in Phase 2 migrations. This baseline establishes the
Alembic version table and migration chain.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
