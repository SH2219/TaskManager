# app/services/project_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.project_repo import project_repo
from app.models.project import Project

class ProjectService:
    """Service layer for Project operations."""

    async def create_project(
        self,
        db: AsyncSession,
        name: str,
        description: str | None = None
    ) -> Project:
        """Create a new project and commit to DB."""
        project = await project_repo.create(db, name=name, description=description)
        await db.commit()  # commit after creating
        return project
    
    async def get_project(self, db: AsyncSession, project_id: int) -> Project | None:
        """Get a project by ID."""
        return await project_repo.get(db, project_id)
    
    async def list_projects(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> list[Project]:
        """List all projects with optional pagination."""
        return await project_repo.list(db, skip=skip, limit=limit)
    
    async def update_project(
        self,
        db: AsyncSession,
        project_id: int,
        patch: dict
    ) -> Project | None:
        """Update a project with given patch and commit."""
        project = await project_repo.update(db, project_id, patch)
        if project:
            await db.commit()
        return project
    
    async def delete_project(self, db: AsyncSession, project_id: int) -> None:
        """Delete a project and commit."""
        await project_repo.delete(db, project_id)
        await db.commit()
    
# module-level instance for easy import
project_service = ProjectService()
