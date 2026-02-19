# app/models/projectmembers.py
from __future__ import annotations
from sqlalchemy import Column, Integer, BigInteger, String, TIMESTAMP, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base

class ProjectMembers(Base):
    __tablename__= "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name= "uq_project_user"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    
    role = Column(String(32), nullable=False)  # e.g. 'member', 'manager', 'owner'
    added_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # convenience relationships
    project = relationship("Project", lazy="select")
    user = relationship("User", foreign_keys=[user_id], lazy="select")
    added_by_user = relationship("User", foreign_keys=[added_by], lazy="select")
    
    def __repr__(self) -> str:
        return f"<ProjectMember id={self.id} project={self.project_id} user={self.user_id} role={self.role!r}>"