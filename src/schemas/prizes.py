from typing import Any

from pydantic import BaseModel

class PrizeCreate(BaseModel):
    place: int
    title: str
    reward: str

class PrizeResponse(BaseModel):
    id: int
    place: int
    title: str
    reward: str

    model_config = {
        "from_attributes": True
    }