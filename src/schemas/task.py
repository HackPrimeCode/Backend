from pydantic import BaseModel, ConfigDict, Field

from src.enums import TaskStatus


class TeamMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    team_id: int
    email: str
    name: str
    skills: list[str] = Field(default_factory=list)
    is_captain: bool
    avatar_color: str | None = None


class TaskAssigneeRead(BaseModel):
    name: str
    color: str


class HackathonTaskRead(BaseModel):
    id: str
    title: str
    tag: str
    description: str
    assignee: TaskAssigneeRead | None = None


class TaskColumnsRead(BaseModel):
    backlog: list[HackathonTaskRead] = Field(default_factory=list)
    in_work: list[HackathonTaskRead] = Field(default_factory=list)
    review: list[HackathonTaskRead] = Field(default_factory=list)
    done: list[HackathonTaskRead] = Field(default_factory=list)


class HackathonTasksRead(BaseModel):
    team_id: str
    team_members: list[TeamMemberRead]
    tasks: TaskColumnsRead


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    tag: str = Field(default="", max_length=64)
    description: str = Field(default="", max_length=5000)
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    tag: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=5000)
    assignee_id: int | None = None
    status: TaskStatus | None = None
    position: int | None = Field(default=None, ge=0)
