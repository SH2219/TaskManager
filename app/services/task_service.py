# app/services/task_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Iterable
from app.repositories.task_repo import task_repo
from app.models.task import Task

class TaskService:
    async def create_task(self, db: AsyncSession, **kwargs) -> Task:
        return await task_repo.create(db, **kwargs)

    async def get_task(self, db: AsyncSession, task_id: int) -> Task | None:
        return await task_repo.get(db, task_id)

    async def list_tasks(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Task]:
        return await task_repo.list(db, skip=skip, limit=limit)

    async def update_task(self, db: AsyncSession, task_id: int, patch: dict) -> Task | None:
        return await task_repo.update(db, task_id, patch)

    async def assign_users(self, db: AsyncSession, task_id: int, user_ids: Iterable[int]) -> Task | None:
        return await task_repo.assign_users(db, task_id, user_ids)


task_service = TaskService()
