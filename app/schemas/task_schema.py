# app/schemas/task_schema.py
from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: int
    parent_task_id: Optional[int] = Field(default=None, description="Optional. Only provide for subtasks")
    assignee_ids: Optional[List[int]] = Field(default_factory=list)
    due_at: Optional[datetime] = None
    start_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = None

    # forbid extra fields on creation payloads
    model_config = {"extra": "forbid"}


class TaskReadBase(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    project_id: int
    parent_task_id: Optional[int] = None
    assignee_ids: List[int] = Field(default_factory=list)
    due_at: Optional[datetime] = None
    tag_ids: List[int] = Field(default_factory=list)   
    comments_count: Optional[int] = None 
    start_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = None
    version: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # allow reading from SQLAlchemy object attributes
    model_config = {"from_attributes": True}


class TaskNested(TaskReadBase):
    subtasks: List["TaskNested"] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_ids: Optional[List[int]] = None
    due_at: Optional[datetime] = None
    parent_task_id: Optional[int] = None
    start_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = None
    version: Optional[int] = None

    model_config = {"from_attributes": True}


class TaskRead(TaskReadBase):
    subtasks: List[TaskNested] = Field(default_factory=list)


# alias expected by other parts of your code
TaskOut = TaskRead

# resolve recursive models (Pydantic v2)
TaskNested.model_rebuild()
TaskRead.model_rebuild()
