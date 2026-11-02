# app/models/task_assignment.py
from sqlalchemy import Column, BigInteger, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class TaskAssignment(Base):
    __tablename__ = "task_assignees"

    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    progress = Column(Integer, nullable=False, server_default="0", default=0)
    rating = Column(Integer, nullable=True)

    task = relationship("Task", back_populates="assignments", lazy="select")
    user = relationship("User", back_populates="assignments", lazy="select")

    @property
    def user_name(self):
        return self.user.name if self.user else None

    @property
    def user_email(self):
        return self.user.email if self.user else None

    @property
    def user_role(self):
        return self.user.role if self.user else None

    def __repr__(self):
        return f"<TaskAssignment task_id={self.task_id} user_id={self.user_id}>"
