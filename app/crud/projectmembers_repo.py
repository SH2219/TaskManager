# app/crud/ProjectMemberss_repo.py
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.projectmembers import ProjectMembers

class ProjectMembersRepo:
    async def get(self, db: AsyncSession, member_id: int) -> Optional[ProjectMembers]:
        q = select(ProjectMembers).where(ProjectMembers.id == member_id)
        result = await db.execute(q)
        return result.scalars().one_or_none()
    
    async def get_by_project_user(self, db: AsyncSession, project_id: int, user_id: int) -> Optional[ProjectMembers]:
        q = select(ProjectMembers).where(ProjectMembers.project_id == project_id, ProjectMembers.user_id == user_id)
        result = await db.execute(q)
        return result.scalars().one_or_none()
    
    async def list_by_project(self, db: AsyncSession, project_id: int, skip: int = 0, limit: int = 100) -> List[ProjectMembers]:
        q = select(ProjectMembers).where(ProjectMembers.project_id == project_id).offset(skip).limit(limit)
        result = await db.execute(q)
        return result.scalars().all()

    async def list_by_user(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[ProjectMembers]:
        q = select(ProjectMembers).where(ProjectMembers.user_id == user_id).offset(skip).limit(limit)
        result = await db.execute(q)
        return result.scalars().all()
    
    async def create(self, db: AsyncSession, *, project_id: int, user_id: int, role: str, added_by: int | None = None) -> ProjectMembers:
        pm = ProjectMembers(project_id=project_id, user_id=user_id, role=role, added_by=added_by)
        db.add(pm)
        await db.flush()
        await db.refresh(pm)
        return pm
    
    async def update(self, db: AsyncSession, pm: ProjectMembers, patch: dict) -> ProjectMembers:
        for k, v in patch.items():
            if hasattr(pm, k):
                setattr(pm, k, v)
        db.add(pm)
        await db.flush()
        await db.refresh(pm)
        return pm
    
    async def delete(self, db: AsyncSession, pm: ProjectMembers) -> None:
        await db.delete(pm)
        await db.flush()


projectmembers_repo = ProjectMembersRepo()