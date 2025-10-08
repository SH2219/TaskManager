# app/schemas/tag_schema.py
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from app.core.database import Base


class TagCreate(BaseModel):
    name:str
    color:Optional[str]=None        
    description:Optional[str]=None
    
    model_config = {"extra": "forbid"}
    
class TagRead(BaseModel):
    id:int
    name:str
    color:Optional[str]=None
    description:Optional[str]=None
    
    model_config = {"from_attributes": True}
    
class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None

    model_config = {"extra": "forbid"}
