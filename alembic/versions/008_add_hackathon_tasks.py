"""008_add_hackathon_tasks

Revision ID: a1b2c3d4e5f6
Revises: 558e5caf1d6d
Create Date: 2026-07-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "558e5caf1d6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    task_status_enum = postgresql.ENUM(
        "backlog",
        "in_work",
        "review",
        "done",
        name="task_status_enum",
        create_type=False,
    )
    task_status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "hackathon_participants",
        sa.Column("avatar_color", sa.String(length=32), nullable=True),
    )

    op.create_table(
        "hackathon_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("tag", sa.String(), nullable=False, server_default=""),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column(
            "status",
            task_status_enum,
            nullable=False,
            server_default="backlog",
        ),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["assignee_id"], ["hackathon_participants.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_hackathon_tasks_team_id"),
        "hackathon_tasks",
        ["team_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_hackathon_tasks_team_id"), table_name="hackathon_tasks")
    op.drop_table("hackathon_tasks")
    op.drop_column("hackathon_participants", "avatar_color")
    op.execute("DROP TYPE IF EXISTS task_status_enum")
