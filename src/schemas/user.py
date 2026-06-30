from pydantic import BaseModel, Field

class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    tech_stack: list[str] | None = Field(default=None, max_length=20)