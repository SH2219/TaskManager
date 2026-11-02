# app/api/v1/routers/__init__.py
# Re-export router objects with consistent names so imports are predictable.

from .users_router import router as users_router
from .tasks_router import router as tasks_router
from .projects_router import router as projects_router
from .tags_router import router as tags_router
from .comments_router import router as comments_router

__all__ = ["users_router", "tasks_router", "projects_router", "tags_router", "comments_router"]
