from typing import Any

from pydantic import BaseModel

class PrizeCreate(BaseModel):
    title: str
    reward: str

class PrizeResponse(BaseModel):
    id: int
    title: str
    reward: str

    model_config = {
        "from_attributes": True
    }