from datetime import datetime

from pydantic import BaseModel

class SubmissionCreate(BaseModel):
    description: str
    repository_url: str
    files: list[str] | None = []

class SubmissionRead(BaseModel):
    id: int
    hackathon_id: int
    team_id: int
    description: str
    repository_url: str
    files: list[str] | None
    submitted_at: datetime

    model_config = {"from_attributes": True}