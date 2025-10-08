# app/models/tag.py
from __future__ import annotations
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.association_tables import task_tags  # shared association table


class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True, unique=True)
    color = Column(String(32), nullable=True)  # e.g., hex color code
    description = Column(Text, nullable=True)
    
    
    # relationship back to Task (Task must reference this secondary too)
    tasks= relationship("Task", secondary=task_tags, back_populates="tags", lazy="select")
    
    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r}>"