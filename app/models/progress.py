# app/models/progress.py
from __future__ import annotations
from sqlalchemy import Column, Integer, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base

class ProgressUpdate(Base):
    __tablename__ = "progress_updates"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # integer percentage 0..100
    value = Column(Integer, nullable=False)
    note = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    task = relationship("Task", back_populates="progress_updates", lazy="select")
    author = relationship("User", lazy="select")

    def __repr__(self) -> str:
        return f"<ProgressUpdate id={self.id} task_id={self.task_id} value={self.value}>"