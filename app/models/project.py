# app/models/project.py
from sqlalchemy import Column, BigInteger, Text, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # one-to-many: project -> tasks
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan", lazy="select")

    def __repr__(self):
        return f"<Project id={self.id} name={self.name}>"
