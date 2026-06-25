from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.hackathon import Hackathon

class HackathonPrize(Base):
    __tablename__ = "hackathon_prizes"

    id: Mapped[int] = mapped_column(primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id", ondelete="CASCADE"))
    
    place: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    reward: Mapped[str] = mapped_column(String(255))

    hackathon: Mapped["Hackathon"] = relationship(back_populates="prizes")