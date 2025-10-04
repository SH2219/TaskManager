# app/services/project_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.project_repo import project_repo
from app.models.project import Project

class ProjectService:
    async def create_project(self, db: AsyncSession, name: str, description: str | None = None) -> Project:
        return await project_repo.create(db, name=name, description=description)
    
    async def get_project(self, db: AsyncSession, project_id: int) -> Project | None:
        return await project_repo.get(db, project_id)
    
    async def list_projects(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Project]:
        return await project_repo.list(db, skip=skip, limit=limit)
    
    async def update_project(self, db: AsyncSession, project_id: int, patch: dict) -> Project | None:
        return await project_repo.update(db, project_id, patch)
    
    async def delete_project(self, db: AsyncSession, project_id: int) -> None:
        await project_repo.delete(db, project_id)
    
project_service = ProjectService()