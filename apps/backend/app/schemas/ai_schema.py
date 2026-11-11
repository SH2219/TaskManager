from typing import Optional

from pydantic import BaseModel, Field


class GenerateTaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    project_id: int = Field(gt=0)
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    due_at: Optional[str] = Field(default=None, max_length=64)
    parent_task_id: Optional[int] = Field(default=None, gt=0)

    model_config = {"extra": "forbid"}


class GenerateTaskOut(BaseModel):
    title: str
    description: str
    source: str = "nvidia"
