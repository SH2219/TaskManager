# app/repositories/project_repo.py
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project

class ProjectRepository:
    """Repository layer for Project CRUD operations."""

    async def create(self, db: AsyncSession, *, name: str, description: str | None = None) -> Project:
        """Create a new project. Do NOT commit here."""
        project = Project(name=name, description=description)
        db.add(project)
        await db.flush()  # assign ID without committing
        await db.refresh(project)
        return project
    
    async def get(self, db: AsyncSession, project_id: int) -> Optional[Project]:
        """Get a project by its ID."""
        result = await db.execute(select(Project).where(Project.id == project_id))
        return result.scalars().first()
    
    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Project]:
        """List projects with pagination."""
        result = await db.execute(select(Project).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def update(self, db: AsyncSession, project_id: int, patch: dict) -> Optional[Project]:
        """Update project fields. Do NOT commit here."""
        project = await self.get(db, project_id)
        if not project:
            return None
        for k, v in patch.items():
            setattr(project, k, v)
        db.add(project)
        await db.flush()  # persist changes without committing
        await db.refresh(project)
        return project

    async def delete(self, db: AsyncSession, project_id: int) -> None:
        """Delete project. Do NOT commit here."""
        await db.execute(delete(Project).where(Project.id == project_id))
        await db.flush()  # flush deletion
    
# module-level instance for easy import
project_repo = ProjectRepository()
