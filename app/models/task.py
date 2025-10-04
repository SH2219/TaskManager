# app/models/task.py
from sqlalchemy import (
    Column, BigInteger, Text, TIMESTAMP, func, ForeignKey, Integer
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.association_tables import task_assignees  # the association table

class Task(Base):
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Text, nullable=False, server_default="todo")
    priority = Column(Integer, server_default="3")

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    project = relationship("Project", back_populates="tasks", lazy="select")
    creator = relationship("User", back_populates="created_tasks", lazy="select")

    # many-to-many: assignees
    assignees = relationship(
        "User",
        secondary=task_assignees,
        back_populates="assigned_tasks",
        lazy="select"
    )

    def __repr__(self):
        return f"<Task id={self.id} title={self.title}>"
