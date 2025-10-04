# app/repositories/task_repo.py
from typing import Optional, Iterable
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.user import User


class TaskRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        title: str,
        project_id: int,
        creator_id: int | None = None,
        description: str | None = None,
        priority: int | None = 3,
        status: str | None = "todo"
    ) -> Task:
        task = Task(
            title=title,
            description=description,
            project_id=project_id,
            creator_id=creator_id,
            priority=priority,
            status=status
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task
    
    
    async def get(self, db: AsyncSession, task_id: int) -> Optional[Task]:
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalars().first()
    
    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Task]:
        result = await db.execute(select(Task).offset(skip).limit(limit))
        return result.scalars().all()
    
    
    async def update(self, db: AsyncSession, task_id: int, patch: dict) -> Optional[Task]:
        task = await self.get(db, task_id)
        if not task:
            return None
        for k, v in patch.items():
            setattr(task, k, v)
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task
    
    async def assign_users(self, db: AsyncSession, task_id: int, user_ids: Iterable[int]) -> Optional[Task]:
        """
        Replace the task's assignees with the users matching user_ids.
        This uses the ORM relationship (assigns the list).
        """
        task = await self.get(db, task_id)
        if not task:
            return None

        if not user_ids:
            # clear assignment
            task.assignees = []
        else:
            # fetch users for the given ids
            result = await db.execute(select(User).where(User.id.in_(list(user_ids))))
            users = result.scalars().all()
            task.assignees = users

        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task


task_repo = TaskRepository()