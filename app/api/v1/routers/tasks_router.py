from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.schemas.task_schema import TaskCreate, TaskOut
from app.services.task_service import task_service
from app.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# Create task
@router.post("/", response_model=TaskOut)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await task_service.create_task(db, title=payload.title, description=payload.description, project_id=payload.project_id)


# List tasks
@router.get("/", response_model=List[TaskOut])
async def list_tasks(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await task_service.list_tasks(db, skip=skip, limit=limit)


# Assign users to task
@router.post("/{task_id}/assign")
async def assign_users(task_id: int, user_ids: List[int], db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    task = await task_service.assign_users(db, task_id, user_ids)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Users assigned successfully"}