from pydantic import BaseModel

class LeaderboardHackathonItem(BaseModel):
    id: int
    title: str

    model_config = {"from_attributes": True}

class TeamLeaderboardRead(BaseModel):
    team_id: int
    team_name: str

    average_score: float

    idea: float
    implementation: float
    quality: float
    design: float