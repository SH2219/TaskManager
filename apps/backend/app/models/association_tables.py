# app/models/association_tables.py
from sqlalchemy import Table, Column, BigInteger, ForeignKey, Integer
from app.core.database import Base

# Association table: tasks <-> tags
task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)
