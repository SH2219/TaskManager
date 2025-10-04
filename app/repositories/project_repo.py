# app/repositories/project_repo.py
from typing import Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project

class ProjectRepository:
    async def create(self, db: AsyncSession, *, name: str, description: str | None = None) -> Project:
        project = Project(name=name, description=description)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
    
    async def get(self, db: AsyncSession, project_id: int) -> Optional[Project]:
        result = await db.execute(select(Project).where(Project.id == project_id))
        return result.scalars().first()
    
    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Project]:
        result = await db.execute(select(Project).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def update(self, db: AsyncSession, project_id: int, patch: dict) -> Optional[Project]:
        project = await self.get(db, project_id)
        if not project:
            return None
        for k, v in patch.items():
            setattr(project, k, v)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    async def delete(self, db: AsyncSession, project_id: int) -> None:
        await db.execute(delete(Project).where(Project.id == project_id))
        await db.commit()
        
project_repo = ProjectRepository()