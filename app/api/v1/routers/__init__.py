# app/api/v1/routers/__init__.py
# Re-export router objects with consistent names so imports are predictable.

from .users_router import router as users_router
from .tasks_router import router as tasks_router
from .projects_router import router as projects_router

__all__ = ["users_router", "tasks_router", "projects_router"]
