# app/models/project_member.py
from sqlalchemy import Column, BigInteger, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(Text, nullable=False, server_default="member", default="member")

    project = relationship("Project", back_populates="members", lazy="select")
    user = relationship("User", back_populates="memberships", lazy="select")

    def __repr__(self):
        return f"<ProjectMember project_id={self.project_id} user_id={self.user_id}>"
