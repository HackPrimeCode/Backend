from pydantic import BaseModel, EmailStr, Field

from src.enums import ParticipantRole

class TeamCreate(BaseModel):
    team_name: str = Field(min_length=1, max_length=255)
    description: str
    invite_emails: list[EmailStr] = Field(default_factory=list)

class TeamInviteRequest(BaseModel):
    emails: list[EmailStr]

class InviteTokenRead(BaseModel):
    token: str
    email: str


class TeamCreateResponse(BaseModel):
    team_id: int
    team_name: str
    description: str
    invite_tokens: list[InviteTokenRead]

class TeamProfileRead(BaseModel):
    id: int
    team_name: str
    members_count: int
    role_in_team: ParticipantRole

    model_config = {"from_attributes": True}