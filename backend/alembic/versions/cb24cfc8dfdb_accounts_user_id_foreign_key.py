"""accounts user_id foreign key + theme normalization

Revision ID: cb24cfc8dfdb
Revises: b269dd11c4b9
Create Date: 2026-11-20 06:02:35.577737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cb24cfc8dfdb"
down_revision: Union[str, None] = "b269dd11c4b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enforce account ownership at the database level (spec §6.3 C / §6.4).
    op.create_foreign_key(
        "fk_accounts_user_id_users",
        "accounts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # Normalise theme values to lowercase to match the spec ("system"/"light"/"dark").
    op.execute("UPDATE user_preferences SET theme = lower(theme)")


def downgrade() -> None:
    op.drop_constraint("fk_accounts_user_id_users", "accounts", type_="foreignkey")
