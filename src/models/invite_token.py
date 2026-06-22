import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.enums import InviteTargetRole
from src.models.enums import enum_values


class InviteToken(Base):
    __tablename__ = "invite_tokens"

    token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, index=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"), index=True)
    target_team_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams.id"), nullable=True
    )
    target_role: Mapped[InviteTargetRole] = mapped_column(
        Enum(
            InviteTargetRole,
            name="invite_target_role_enum",
            native_enum=True,
            values_callable=enum_values,
        )
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)

    hackathon: Mapped["Hackathon"] = relationship(back_populates="invite_tokens")
    target_team: Mapped["Team | None"] = relationship(back_populates="invite_tokens")
