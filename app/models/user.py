# app/models/user.py
from sqlalchemy import Column, BigInteger, Text, TIMESTAMP, func
from sqlalchemy.orm import relationship
from core.database import Base
from app.models.association_tables import task_assignees  # import the Table object

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(Text, unique=True, nullable=False, index=True)
    name = Column(Text, nullable=True)
    password_hash = Column(Text, nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # tasks that this user created (one-to-many)
    created_tasks = relationship("Task", back_populates="creator", lazy="select")

    # tasks this user is assigned to (many-to-many via task_assignees)
    assigned_tasks = relationship(
        "Task",
        secondary=task_assignees,
        back_populates="assignees",
        lazy="select"
    )

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"
