# app/schemas/comment_schema.py
from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CommentCreate(BaseModel):
    task_id:int
    content:str
    
    model_config = {"extra": "forbid"}
    
class CommentRead(BaseModel):
    id:int
    task_id:int
    user_id:Optional[int]=None
    content:str
    created_at:Optional[datetime]=None
    updated_at:Optional[datetime]=None
    
    # optional: include author summary later (id/name/email) if you want nested author info

    model_config = {"from_attributes": True}
    
class CommentUpdate(BaseModel):
    content: Optional[str] = None

    model_config = {"extra": "forbid"}