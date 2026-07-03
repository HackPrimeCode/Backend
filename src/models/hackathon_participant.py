from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.enums import ParticipantRole
from src.models.enums import enum_values


class HackathonParticipant(Base):
    __tablename__ = "hackathon_participants"
    __table_args__ = (
        UniqueConstraint("user_id", "hackathon_id", name="uq_user_hackathon"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    role: Mapped[ParticipantRole] = mapped_column(
        Enum(
            ParticipantRole,
            name="participant_role_enum",
            native_enum=True,
            values_callable=enum_values,
        )
    )
    avatar_color: Mapped[str | None] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="hackathon_participations")
    hackathon: Mapped["Hackathon"] = relationship(back_populates="participants")
    team: Mapped["Team | None"] = relationship(back_populates="participants")
    assigned_tasks: Mapped[list["HackathonTask"]] = relationship(
        back_populates="assignee",
        foreign_keys="HackathonTask.assignee_id",
    )
