from datetime import datetime

from sqlalchemy import DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.enums import HackathonStatus
from src.models.enums import enum_values


class Hackathon(Base):
    __tablename__ = "hackathons"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[HackathonStatus] = mapped_column(
        Enum(
            HackathonStatus,
            name="hackathon_status_enum",
            native_enum=True,
            values_callable=enum_values,
        ),
        default=HackathonStatus.DRAFT,
    )
    submission_requirements: Mapped[list | None] = mapped_column(JSONB, default=list)
    evaluation_criteria: Mapped[list | None] = mapped_column(JSONB, default=list)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    tz_file_url: Mapped[str | None] = mapped_column(default=None)

    teams: Mapped[list["Team"]] = relationship(back_populates="hackathon")
    participants: Mapped[list["HackathonParticipant"]] = relationship(
        back_populates="hackathon"
    )
    invite_tokens: Mapped[list["InviteToken"]] = relationship(back_populates="hackathon")
