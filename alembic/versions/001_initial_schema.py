"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    global_role_enum = postgresql.ENUM(
        "admin", "user", "organizator", name="global_role_enum", create_type=False
    )
    hackathon_status_enum = postgresql.ENUM(
        "DRAFT",
        "REGISTRATION",
        "IN_PROGRESS",
        "FINISHED",
        name="hackathon_status_enum",
        create_type=False,
    )
    participant_role_enum = postgresql.ENUM(
        "captain", "participant", "judge", name="participant_role_enum", create_type=False
    )
    invite_target_role_enum = postgresql.ENUM(
        "participant", "judge", name="invite_target_role_enum", create_type=False
    )

    global_role_enum.create(op.get_bind(), checkfirst=True)
    hackathon_status_enum.create(op.get_bind(), checkfirst=True)
    participant_role_enum.create(op.get_bind(), checkfirst=True)
    invite_target_role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("tech_stack", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "global_role",
            global_role_enum,
            nullable=False,
            server_default="user",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "hackathons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            hackathon_status_enum,
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column(
            "submission_requirements",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "evaluation_criteria",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hackathon_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["hackathon_id"], ["hackathons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teams_hackathon_id"), "teams", ["hackathon_id"], unique=False)

    op.create_table(
        "hackathon_participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("hackathon_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("role", participant_role_enum, nullable=False),
        sa.ForeignKeyConstraint(["hackathon_id"], ["hackathons.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "hackathon_id", name="uq_user_hackathon"),
    )
    op.create_index(
        op.f("ix_hackathon_participants_hackathon_id"),
        "hackathon_participants",
        ["hackathon_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_hackathon_participants_user_id"),
        "hackathon_participants",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "invite_tokens",
        sa.Column("token", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hackathon_id", sa.Integer(), nullable=False),
        sa.Column("target_team_id", sa.Integer(), nullable=True),
        sa.Column("target_role", invite_target_role_enum, nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["hackathon_id"], ["hackathons.id"]),
        sa.ForeignKeyConstraint(["target_team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("token"),
    )
    op.create_index(op.f("ix_invite_tokens_email"), "invite_tokens", ["email"], unique=False)
    op.create_index(
        op.f("ix_invite_tokens_hackathon_id"), "invite_tokens", ["hackathon_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_invite_tokens_hackathon_id"), table_name="invite_tokens")
    op.drop_index(op.f("ix_invite_tokens_email"), table_name="invite_tokens")
    op.drop_table("invite_tokens")

    op.drop_index(op.f("ix_hackathon_participants_user_id"), table_name="hackathon_participants")
    op.drop_index(
        op.f("ix_hackathon_participants_hackathon_id"), table_name="hackathon_participants"
    )
    op.drop_table("hackathon_participants")

    op.drop_index(op.f("ix_teams_hackathon_id"), table_name="teams")
    op.drop_table("teams")

    op.drop_table("hackathons")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS invite_target_role_enum")
    op.execute("DROP TYPE IF EXISTS participant_role_enum")
    op.execute("DROP TYPE IF EXISTS hackathon_status_enum")
    op.execute("DROP TYPE IF EXISTS global_role_enum")
