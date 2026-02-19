# app/schemas/projectmember_schema.py
from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ProjectMemberCreate(BaseModel):
    project_id: int
    user_id: int
    role: str = Field(..., description="Role in project: e.g. 'member','manager','owner'")

    model_config = {"extra": "forbid"}

class ProjectMemberUpdate(BaseModel):
    role: Optional[str] = None

    model_config = {"extra": "forbid"}


class ProjectMemberRead(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: str
    added_by: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}