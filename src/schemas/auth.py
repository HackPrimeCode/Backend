from pydantic import BaseModel, ConfigDict, EmailStr, Field
from uuid import UUID

from src.enums import GlobalRole


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(TokenResponse):
    user: "UserRead"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    global_role: GlobalRole

class InviteExchangeRequest(BaseModel):
    token: UUID

class PendingInvite(BaseModel):
    invite_id: UUID
    hackathon_id: int
    team_name: str | None
    target_role: str


class InviteExchangeResponse(BaseModel):
    access_token: str
    pending_invite: PendingInvite

class InviteJudgesRequest(BaseModel):
    emails: list[EmailStr]


class InviteJudgesResponse(BaseModel):
    created_invites: list[str]