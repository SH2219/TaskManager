# app/models/association_tables.py
from sqlalchemy import Table, Column, BigInteger, ForeignKey, Integer
from app.core.database import Base  # Base must be the same declarative base used for models

# association table connecting tasks <-> users (assignees)
task_assignees = Table(
    "task_assignees",
    Base.metadata,
    Column("task_id", BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    # you can add columns like assigned_at or assigned_by here if you need them
)

# Association table: tasks <-> tags
task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)