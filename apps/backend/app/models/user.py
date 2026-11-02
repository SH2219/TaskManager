# app/models/user.py
from sqlalchemy import Column, BigInteger, Text, TIMESTAMP, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(Text, unique=True, nullable=False, index=True)
    name = Column(Text, nullable=True)
    phone = Column(Text, nullable=True)
    role = Column(Text, nullable=False, server_default="member")
    password_hash = Column(Text, nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    created_tasks = relationship("Task", back_populates="creator", lazy="select")
    assignments = relationship("TaskAssignment", back_populates="user", lazy="select")
    memberships = relationship("ProjectMember", back_populates="user", lazy="select")

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"
