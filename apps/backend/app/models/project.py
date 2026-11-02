# app/models/project.py
from typing import List

from sqlalchemy import Column, BigInteger, Text, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    archived_at = Column(TIMESTAMP(timezone=True), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan", lazy="select")
    members = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def archived(self) -> bool:
        return self.archived_at is not None

    @property
    def member_ids(self) -> List[int]:
        """Member ids when members are loaded; otherwise empty (no async lazy IO)."""
        try:
            from sqlalchemy import inspect as sa_inspect
            if "members" in sa_inspect(self).unloaded:
                return []
        except Exception:
            return []
        return [m.user_id for m in (self.members or [])]

    def __repr__(self):
        return f"<Project id={self.id} name={self.name}>"
