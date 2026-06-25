from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.enums import GlobalRole, HackathonStatus
from src.schemas.prizes import PrizeCreate, PrizeResponse
from src.schemas.topic import TopicCreate, TopicResponse


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
    start_date: datetime | None = None
    end_date: datetime | None = None
    prizes: list[PrizeCreate] = Field(default_factory=list)
    technologies: list[Any] = Field(default_factory=list)
    topics: list[TopicCreate] = Field(default_factory=list)
    submission_requirements: list[Any] = Field(default_factory=list)
    evaluation_criteria: list[Any] = Field(default_factory=list)


class HackathonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
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
    prizes: list[PrizeResponse] | None = None
    topics: list[TopicResponse] | None = None
    technologies: list[Any] | None = None
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
    start_date: datetime | None = None
    end_date: datetime | None = None
    tz_file_url: str | None = None


class HackathonDetailRead(HackathonPublicRead):
    prizes: list[PrizeResponse] | None = None
    topics: list[TopicResponse] | None = None
    technologies: list[Any] | None = None
    submission_requirements: list[Any] | None = None
    evaluation_criteria: list[Any] | None = None
