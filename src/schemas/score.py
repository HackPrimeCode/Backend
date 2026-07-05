from pydantic import BaseModel, Field

class JudgeScoreCreate(BaseModel):
    idea: int = Field(ge=1, le=10)
    implementation: int = Field(ge=1, le=10)
    quality: int = Field(ge=1, le=10)
    design: int = Field(ge=1, le=10)