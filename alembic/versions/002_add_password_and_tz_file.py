"""Add password hash and hackathon tz file url

Revision ID: 002
Revises: 001
Create Date: 2026-06-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("hashed_password", sa.String(), nullable=True))
    op.execute("UPDATE users SET hashed_password = '' WHERE hashed_password IS NULL")
    op.alter_column("users", "hashed_password", nullable=False)

    op.add_column("hackathons", sa.Column("tz_file_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("hackathons", "tz_file_url")
    op.drop_column("users", "hashed_password")
