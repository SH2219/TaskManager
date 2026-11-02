from pydantic import BaseModel, Field


class GenerateTaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    model_config = {"extra": "forbid"}


class GenerateTaskOut(BaseModel):
    title: str
    description: str
