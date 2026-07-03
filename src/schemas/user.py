from pydantic import BaseModel, Field

from src.enums import GlobalRole
from src.schemas.hackathon import HackathonRead

class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    tech_stack: list[str] | None = Field(default=None, max_length=20)

class UserProfileRead(BaseModel):
    id: int
    email: str
    name: str | None
    tech_stack: list[str] | None
    global_role: GlobalRole

    active_hackathon: HackathonRead | None
    past_hackathons: list[HackathonRead]

    model_config = {"from_attributes": True}