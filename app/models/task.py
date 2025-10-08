# app/models/task.py
from __future__ import annotations
from typing import List

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

from app.core.database import Base
from app.models.association_tables import task_assignees, task_tags


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

    # tags many-to-many (make sure Tag.tasks has back_populates="tags")
    tags = relationship(
        "Tag",
        secondary=task_tags,
        back_populates="tasks",
        lazy="select",
    )

    # comments one-to-many (make sure Comment.task has back_populates="comments" or "task")
    comments = relationship(
        "Comment",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # self-referential relationship: parent and subtasks
    parent = relationship("Task", remote_side=[id], backref="subtasks")

    def __repr__(self):
        return f"<Task id={self.id} title={self.title!r}>"

    # ---------- helper properties for safe pydantic serialization ----------
    @property
    def assignee_ids(self) -> List[int]:
        """
        Return list of user ids for assignees.
        This lets Pydantic (from_attributes=True) read `assignee_ids` directly
        without triggering lazy SQL loads.
        """
        if self.assignees is None:
            return []
        return [u.id for u in self.assignees]

    @property
    def tag_ids(self) -> List[int]:
        """
        Return list of tag ids attached to the task.
        Used to avoid lazy-loading full Tag objects during serialization.
        """
        if self.tags is None:
            return []
        return [t.id for t in self.tags]

    @property
    def comments_count(self) -> int:
        """
        Return number of comments if relationship is loaded; otherwise returns 0.
        If you want exact count without loading comments, query COUNT in service instead.
        """
        try:
            return len(self.comments or [])
        except Exception:
            return 0

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
            "tag_ids": self.tag_ids,
            "comments_count": self.comments_count,
            "due_at": self.due_at,
            "start_at": self.start_at,
            "estimated_minutes": self.estimated_minutes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
