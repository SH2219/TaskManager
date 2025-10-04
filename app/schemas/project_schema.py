# app/schemas/project_schema.py
from typing import Optional
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    # Pydantic v2: read from ORM objects
    model_config = {"from_attributes": True}

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}

# Backwards-compatible alias used by some routers that expect ProjectOut
ProjectOut = ProjectRead
