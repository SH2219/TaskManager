from typing import List, Optional

from pydantic import BaseModel, Field


class AssignUsersBody(BaseModel):
    user_ids: List[int] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class TaskAssignmentUpdate(BaseModel):
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    rating: Optional[int] = Field(default=None, ge=1, le=5)

    model_config = {"extra": "forbid"}


class TaskAssignmentOut(BaseModel):
    user_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    progress: int = 0
    rating: Optional[int] = None

    model_config = {"from_attributes": True}
