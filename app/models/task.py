# app/models/task.py
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    Text,
    TIMESTAMP,
    func,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.orm import relationship

from core.database import Base
from app.models.association_tables import task_assignees

class Task(Base):
    __tablename__ = "tasks"

    __table_args__ = (
        Index("ix_tasks_project_id_status_due_at", "project_id", "status", "due_at"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    status = Column(Text, nullable=False, server_default=text("'todo'"))
    priority = Column(Integer, server_default=text("3"))

    due_at = Column(TIMESTAMP(timezone=True), nullable=True)
    start_at = Column(TIMESTAMP(timezone=True), nullable=True)
    estimated_minutes = Column(Integer, nullable=True)

    # parent pointer for subtasks - references same table
    parent_task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    project = relationship("Project", back_populates="tasks", lazy="select")
    creator = relationship("User", back_populates="created_tasks", lazy="select")

    assignees = relationship(
        "User",
        secondary=task_assignees,
        back_populates="assigned_tasks",
        lazy="select",
    )

    # self-referential relationship: parent and subtasks
    parent = relationship("Task", remote_side=[id], backref="subtasks")

    def __repr__(self):
        return f"<Task id={self.id} title={self.title!r}>"

    # ---------- NEW: expose assignee IDs so pydantic can read them directly ----------
    @property
    def assignee_ids(self) -> list[int]:
        """
        Return list of user ids for assignees.
        This lets Pydantic (from_attributes=True) read `assignee_ids` directly.
        """
        # guard: assignees may be None or not yet loaded
        if self.assignees is None:
            return []
        return [u.id for u in self.assignees]

    def to_dict(self) -> dict:
        """
        Optional helper for debugging — serializes a subset of task fields.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "parent_task_id": self.parent_task_id,
            "assignee_ids": self.assignee_ids,
            "due_at": self.due_at,
            "start_at": self.start_at,
            "estimated_minutes": self.estimated_minutes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
