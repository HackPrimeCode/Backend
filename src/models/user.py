from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.enums import GlobalRole
from src.models.enums import enum_values


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str | None] = mapped_column(nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(nullable=True)
    tech_stack: Mapped[list | None] = mapped_column(JSONB, default=list)
    global_role: Mapped[GlobalRole] = mapped_column(
        Enum(
            GlobalRole,
            name="global_role_enum",
            native_enum=True,
            values_callable=enum_values,
        ),
        default=GlobalRole.USER,
    )

    hackathon_participations: Mapped[list["HackathonParticipant"]] = relationship(
        back_populates="user"
    )
