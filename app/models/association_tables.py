# app/models/association_tables.py
from sqlalchemy import Table, Column, BigInteger, ForeignKey
from app.database import Base

# Many-to-many: task <-> user (assignees)
task_assignees = Table(
    "task_assignees",
    Base.metadata,
    Column("task_id", BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

# (Optional) If you later add tags, keep this here:
# task_tags = Table(
#     "task_tags",
#     Base.metadata,
#     Column("task_id", BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
#     Column("tag_id", BigInteger, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
# )
