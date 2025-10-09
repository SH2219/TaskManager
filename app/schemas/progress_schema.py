# app/schemas/progress_schema.py
from __future__ import annotations
from typing import Optional, TypeAlias
from datetime import datetime
from pydantic import BaseModel, Field, conint

# 0..100 inclusive integer
Pct: TypeAlias = conint(ge=0, le=100)

class ProgressCreate(BaseModel):
    task_id: int
    value: Pct = Field(..., description="Progress percentage 0..100")
    note: Optional[str] = None

    model_config = {"extra": "forbid"}


class ProgressUpdate(BaseModel):
    value: Optional[Pct] = Field(None, description="Progress percentage 0..100")
    note: Optional[str] = None

    model_config = {"extra": "forbid"}


class ProgressRead(BaseModel):
    id: int
    task_id: int
    user_id: Optional[int] = None
    value: int
    note: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
