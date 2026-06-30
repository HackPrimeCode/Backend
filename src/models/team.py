from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"), index=True)
    name: Mapped[str]
    description: Mapped[str] = mapped_column(nullable=True)
    hackathon: Mapped["Hackathon"] = relationship(back_populates="teams")
    participants: Mapped[list["HackathonParticipant"]] = relationship(
        back_populates="team"
    )
    invite_tokens: Mapped[list["InviteToken"]] = relationship(back_populates="target_team")
