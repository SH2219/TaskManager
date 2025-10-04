# app/schemas/task_schema.py
from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: int
    assignee_ids: List[int] = []
    due_at: Optional[datetime] = None
    start_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = None

    model_config = {"from_attributes": True}


class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    project_id: int
    assignee_ids: List[int] = []
    due_at: Optional[datetime] = None
    start_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = None
    version: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_ids: Optional[List[int]] = None
    due_at: Optional[datetime] = None
    start_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = None
    version: Optional[int] = None

    model_config = {"from_attributes": True}


# Backwards-compatible alias (some code expects TaskOut)
TaskOut = TaskRead
