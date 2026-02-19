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
    parent_task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)

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

    # tags many-to-many
    tags = relationship(
        "Tag",
        secondary=task_tags,
        back_populates="tasks",
        lazy="select",
    )

    # comments one-to-many
    comments = relationship(
        "Comment",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Explicit self-referential relationship: parent <-> subtasks
    # - `parent` is a single parent Task
    # - `subtasks` is a list of children Tasks
    # Use foreign_keys to be explicit and back_populates for clarity.
    parent = relationship(
        "Task",
        remote_side=[id],
        back_populates="subtasks",
        lazy="select",
        foreign_keys=[parent_task_id],
    )

    subtasks = relationship(
        "Task",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="select",
        foreign_keys=[parent_task_id],
        order_by="Task.id",
    )

    # progress percentage on the task (0 to 100). Use text("0") server_default for DB compatibility.
    progress_percentage = Column(Integer, nullable=False, server_default=text("0"))

    # history of progress changes (1..n)
    progress_updates = relationship(
        "ProgressUpdate",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<Task id={self.id} title={self.title!r}>"

    # ---------- helper properties for safe pydantic serialization ----------
    @property
    def assignee_ids(self) -> List[int]:
        """
        Return list of assignee ids without triggering lazy-load IO when the relationship
        is not present on the instance. If the relationship was not loaded, return an
        empty list (caller should ensure eager-loading when real values are needed).
        """
        if "assignees" not in self.__dict__ or self.assignees is None:
            return []
        return [u.id for u in self.assignees]

    @property
    def tag_ids(self) -> List[int]:
        """Same pattern as assignee_ids: avoid triggering lazy loads by checking __dict__."""
        if "tags" not in self.__dict__ or self.tags is None:
            return []
        return [t.id for t in self.tags]

    @property
    def comments_count(self) -> int:
        try:
            if "comments" not in self.__dict__ or self.comments is None:
                return 0
            return len(self.comments)
        except Exception:
            return 0

    @property
    def progress_history_count(self) -> int:
        try:
            if "progress_updates" not in self.__dict__ or self.progress_updates is None:
                return 0
            return len(self.progress_updates)
        except Exception:
            return 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "parent_task_id": self.parent_task_id,
            "assignee_ids": self.assignee_ids,
            "tag_ids": self.tag_ids,
            "comments_count": self.comments_count,
            "progress_percentage": int(self.progress_percentage or 0),
            "progress_history_count": self.progress_history_count,
            "due_at": self.due_at,
            "start_at": self.start_at,
            "estimated_minutes": self.estimated_minutes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
