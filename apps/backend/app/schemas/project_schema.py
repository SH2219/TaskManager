# app/schemas/project_schema.py
from typing import List, Optional
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectMembersBody(BaseModel):
    user_ids: List[int] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

class ProjectRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    archived: bool = False
    member_ids: List[int] = Field(default_factory=list)

    # Pydantic v2: read from ORM objects
    model_config = {"from_attributes": True}


class ProjectDashboardOut(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    archived: bool = False
    progress: int = 0
    task_count: int = 0
    completed_count: int = 0
    open_count: int = 0
    member_count: int = 0

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}

# Backwards-compatible alias used by some routers that expect ProjectOut
ProjectOut = ProjectRead
