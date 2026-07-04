from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from src.enums import ParticipantRole, HackathonStatus

class TeamCreate(BaseModel):
    team_name: str = Field(min_length=1, max_length=255)
    description: str
    invite_emails: list[EmailStr] = Field(default_factory=list)

class TeamInviteRequest(BaseModel):
    emails: list[EmailStr]

class InviteTokenRead(BaseModel):
    token: str
    email: str

    model_config = {"from attributes": True}


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

class TeamMemberRead(BaseModel):
    id: int
    name: str | None
    role: ParticipantRole

    model_config = {"from_attributes": True}

class HackathonShortRead(BaseModel):
    id: int
    title: str
    status: HackathonStatus
    start_date: datetime | None
    end_date: datetime | None
    max_team_size: int | None
    max_participants: int | None

    model_config = {"from_attributes": True}

class TeamDetailRead(BaseModel):
    id: int
    name: str
    hackathon: HackathonShortRead

    members: list[TeamMemberRead]
    members_count: int
    max_team_size: int | None

    pending_invites: list[InviteTokenRead]

    model_config = {"from_attributes": True}

class TeamUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)