from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.enums import GlobalRole, HackathonStatus, HackPlace
from src.schemas.prizes import PrizeCreate, PrizeResponse


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    tech_stack: list[Any] | None = None
    global_role: GlobalRole


class HackathonCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    place: HackPlace | None = None
    min_team_size: int | None = None
    max_team_size: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    prizes: list[PrizeCreate] = Field(default_factory=list)
    topics: list[Any] = Field(default_factory=list)
    max_participants: int | None = None
    submission_requirements: list[Any] = Field(default_factory=list)
    evaluation_criteria: list[Any] = Field(default_factory=list)


class HackathonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    topics: list[Any] | None = None
    prizes: list[PrizeCreate] | None = None
    submission_requirements: list[Any] | None = None
    evaluation_criteria: list[Any] | None = None


class HackathonStatusUpdate(BaseModel):
    status: HackathonStatus


class HackathonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    status: HackathonStatus
    place: HackPlace
    prizes: list[PrizeResponse] | None = None
    topics: list[Any] | None = None
    current_participants: int = 0
    current_teams: int = 0
    min_team_size: int | None = None
    max_team_size: int | None = None
    max_participants: int | None = None
    submission_requirements: list[Any] | None = None
    evaluation_criteria: list[Any] | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    tz_file_url: str | None = None


class HackathonPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    status: HackathonStatus
    place: HackPlace
    prizes: list[PrizeResponse] | None = None
    topics: list[Any] | None = None
    current_participants: int = 0
    current_teams: int = 0
    min_team_size: int | None = None
    max_team_size: int | None = None
    max_participants: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    tz_file_url: str | None = None
    submission_requirements: list[Any] | None = None
    evaluation_criteria: list[Any] | None = None

class HackathonShortRead(BaseModel):
    id: int
    title: str
    status: HackathonStatus
    start_date: datetime | None
    end_date: datetime | None
    max_team_size: int | None
    max_participants: int | None

    model_config = {"from_attributes": True}