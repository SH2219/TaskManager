# app/models/association_tables.py
from sqlalchemy import Table, Column, BigInteger, ForeignKey
from core.database import Base  # Base must be the same declarative base used for models

# association table connecting tasks <-> users (assignees)
task_assignees = Table(
    "task_assignees",
    Base.metadata,
    Column("task_id", BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    # you can add columns like assigned_at or assigned_by here if you need them
)
