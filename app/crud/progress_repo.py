# app/crud/progress_repo.py
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress import ProgressUpdate

class ProgressRepo:
    async def get(self, db: AsyncSession, progress_id: int) -> Optional[ProgressUpdate]:
        q = select(ProgressUpdate).where(ProgressUpdate.id == progress_id)
        result = await db.execute(q)
        return result.scalars().one_or_none()

    async def list_by_task(self, db: AsyncSession, task_id: int, skip: int = 0, limit: int = 100) -> List[ProgressUpdate]:
        q = (
            select(ProgressUpdate)
            .where(ProgressUpdate.task_id == task_id)
            .order_by(ProgressUpdate.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(q)
        return result.scalars().all()

    async def list_recent_by_task(self, db: AsyncSession, task_id: int, limit: int = 10) -> List[ProgressUpdate]:
        q = (
            select(ProgressUpdate)
            .where(ProgressUpdate.task_id == task_id)
            .order_by(ProgressUpdate.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(q)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, task_id: int, user_id: int | None, value: int, note: str | None) -> ProgressUpdate:
        pu = ProgressUpdate(task_id=task_id, user_id=user_id, value=value, note=note)
        db.add(pu)
        await db.flush()
        await db.refresh(pu)
        return pu

    async def update(self, db: AsyncSession, progress: ProgressUpdate, patch: dict) -> ProgressUpdate:
        for k, v in patch.items():
            if hasattr(progress, k):
                setattr(progress, k, v)
        db.add(progress)
        await db.flush()
        await db.refresh(progress)
        return progress

    async def delete(self, db: AsyncSession, progress: ProgressUpdate) -> None:
        await db.delete(progress)
        await db.flush()


progress_repo = ProgressRepo()