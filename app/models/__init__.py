# app/models/__init__.py
# Export model classes so other code can import from app.models
from .user import User
from .project import Project
from .task import Task

__all__ = ["User", "Project", "Task"]
