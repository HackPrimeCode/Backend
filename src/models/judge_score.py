from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base

class JudgeScore(Base):
    __tablename__ = "judge_scores"

    id: Mapped[int] = mapped_column(primary_key=True)

    hackathon_id: Mapped[int] = mapped_column(
        ForeignKey("hackathons.id", ondelete="CASCADE"),
        index=True,
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        index=True,
    )

    judge_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    idea: Mapped[int]
    implementation: Mapped[int]
    quality: Mapped[int]
    design: Mapped[int]

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint("team_id", "judge_id", name="unique_judge_score"),
    )