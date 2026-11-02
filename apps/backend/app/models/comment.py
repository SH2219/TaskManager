# app/models/comment.py
from __future__ import annotations
from sqlalchemy import Column, Integer, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)   
    
    # relationships\
    task = relationship("Task", back_populates="comments", lazy="select")
    author = relationship("User",  lazy="select")
    
    def __repr__(self) -> str:
        return f"<Comment id={self.id} task_id={self.task_id} user_id={self.user_id}>"