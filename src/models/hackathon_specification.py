from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class HackathonSpecification(Base):
    __tablename__ = "hackathon_specifications"

    id: Mapped[int] = mapped_column(primary_key=True)

    hackathon_id: Mapped[int] = mapped_column(
        ForeignKey("hackathons.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )

    task: Mapped[str] = mapped_column(Text)
    task_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    functional_requirements: Mapped[list[str] | None] = mapped_column(
        JSONB, default=list
    )

    technical_limitations: Mapped[list[str] | None] = mapped_column(
        JSONB, default=list
    )

    evaluation_criteria: Mapped[list[str] | None] = mapped_column(
        JSONB, default=list
    )

    files: Mapped[list[str] | None] = mapped_column(
        JSONB, default=list
    )

    hackathon: Mapped["Hackathon"] = relationship(
        back_populates="specification"
    )