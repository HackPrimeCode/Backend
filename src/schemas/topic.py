from pydantic import BaseModel


class TopicCreate(BaseModel):
    name: str
    description: str | None = None

class TopicResponse(BaseModel):
    id: int
    name: str
    description: str | None

    model_config = {
        "from_attributes": True
    }