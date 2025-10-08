# app/models/__init__.py
# Export model classes so other code can import from app.models
from .user import User
from .project import Project
from .task import Task
from .tag import Tag
from .comment import Comment

__all__ = ["User", "Project", "Task", "Tag", "Comment"]
