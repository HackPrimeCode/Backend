from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.enums import TaskStatus
from src.models.enums import enum_values


class HackathonTask(Base):
    __tablename__ = "hackathon_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str]
    tag: Mapped[str] = mapped_column(default="")
    description: Mapped[str] = mapped_column(default="")
    status: Mapped[TaskStatus] = mapped_column(
        Enum(
            TaskStatus,
            name="task_status_enum",
            native_enum=True,
            values_callable=enum_values,
        ),
        default=TaskStatus.BACKLOG,
    )
    position: Mapped[int] = mapped_column(default=0)
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("hackathon_participants.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    team: Mapped["Team"] = relationship(back_populates="tasks")
    assignee: Mapped["HackathonParticipant | None"] = relationship(
        back_populates="assigned_tasks",
        foreign_keys=[assignee_id],
    )
