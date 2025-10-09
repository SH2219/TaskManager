# app/services/progress_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict

from app.crud.progress_repo import progress_repo
from app.crud.task_repo import task_repo   # adjust import path if your task repo lives elsewhere
from app.models.progress import ProgressUpdate
from sqlalchemy.orm import selectinload

class ProgressService:
    async def create_progress(self, db: AsyncSession, creator_user_id: int, *, task_id: int, value: int, note: Optional[str] = None) -> ProgressUpdate:
        # Basic validation
        if value is None:
            raise ValueError("Progress value required")
        if not (0 <= int(value) <= 100):
            raise ValueError("Progress value must be between 0 and 100")

        # Ensure task exists
        task = await task_repo.get(db, task_id)
        if not task:
            raise ValueError(f"Task not found (id={task_id})")

        # create progress update
        pu = await progress_repo.create(db, task_id=task_id, user_id=creator_user_id, value=int(value), note=note)

        # update the task's progress_percentage to reflect new value
        task.progress_percentage = int(value)
        db.add(task)

        # commit and refresh both
        await db.commit()
        await db.refresh(pu)
        await db.refresh(task)
        return pu

    async def get_progress(self, db: AsyncSession, progress_id: int) -> Optional[ProgressUpdate]:
        return await progress_repo.get(db, progress_id)

    async def list_progress_for_task(self, db: AsyncSession, task_id: int, skip: int = 0, limit: int = 100) -> List[ProgressUpdate]:
        return await progress_repo.list_by_task(db, task_id, skip=skip, limit=limit)

    async def list_recent_for_task(self, db: AsyncSession, task_id: int, limit: int = 10) -> List[ProgressUpdate]:
        return await progress_repo.list_recent_by_task(db, task_id, limit=limit)

    async def update_progress(self, db: AsyncSession, progress_id: int, patch: Dict, requester_user_id: int) -> Optional[ProgressUpdate]:
        progress = await progress_repo.get(db, progress_id)
        if not progress:
            return None

        # Permission check: only author may edit (change as per your policy)
        if progress.user_id is not None and progress.user_id != requester_user_id:
            raise PermissionError("Not allowed to edit this progress update")

        # If value present, validate 0..100 and update task progress_percentage as well
        new_value = patch.get("value")
        if new_value is not None:
            if not (0 <= int(new_value) <= 100):
                raise ValueError("Progress value must be between 0 and 100")

        progress = await progress_repo.update(db, progress, patch)

        # If value changed, propagate to task
        if new_value is not None:
            task = await task_repo.get(db, progress.task_id)
            if task:
                task.progress_percentage = int(new_value)
                db.add(task)

        await db.commit()
        await db.refresh(progress)
        if new_value is not None and task:
            await db.refresh(task)
        return progress

    async def delete_progress(self, db: AsyncSession, progress_id: int, requester_user_id: int) -> None:
        progress = await progress_repo.get(db, progress_id)
        if not progress:
            raise ValueError("Progress update not found")

        # permission: only author may delete
        if progress.user_id is not None and progress.user_id != requester_user_id:
            raise PermissionError("Not allowed to delete this progress update")

        # If deleting the latest progress update you'd probably want to recompute the task.progress_percentage.
        # For simplicity here we will delete the update and NOT modify the task progress. You can extend this.
        await progress_repo.delete(db, progress)
        await db.commit()

progress_service = ProgressService()