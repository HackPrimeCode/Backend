from datetime import datetime
from sqlalchemy import ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from src.core.database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)

    hackathon_id: Mapped[int] = mapped_column(
        ForeignKey("hackathons.id", ondelete="CASCADE"),
        index=True,
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )

    description: Mapped[str] = mapped_column(Text)
    repository_url: Mapped[str] = mapped_column(Text)

    files: Mapped[list[str] | None] = mapped_column(JSONB, default=list)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    team: Mapped["Team"] = relationship()
    hackathon: Mapped["Hackathon"] = relationship()