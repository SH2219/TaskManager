# app/api/v1/routers/tasks_router.py
from typing import List
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Body, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from app.schemas.task_schema import TaskCreate, TaskUpdate, TaskOut
from app.services.task_service import task_service
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Normalize/validate parent id
    parent_id = getattr(payload, "parent_task_id", None)
    if parent_id is not None:
        try:
            parent_id = int(parent_id)
            if parent_id <= 0:
                parent_id = None
        except (TypeError, ValueError):
            parent_id = None

    try:
        task = await task_service.create_task(
            db=db,
            creator_id=current_user.id,
            title=payload.title,
            description=payload.description,
            project_id=payload.project_id,
            parent_task_id=parent_id,
            assignee_ids=payload.assignee_ids,
            priority=getattr(payload, "priority", None),
            due_at=payload.due_at,
            start_at=payload.start_at,
            estimated_minutes=payload.estimated_minutes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Explicitly validate/convert ORM -> Pydantic model
    try:
        return TaskOut.model_validate(task, from_attributes=True)
    except Exception:
        try:
            logger.exception("Failed to serialize Task to TaskOut: %s", getattr(task, "to_dict", lambda: repr(task))())
        except Exception:
            logger.exception("Failed to serialize Task (to_dict() failed). Task repr: %s", repr(task))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while serializing task")


@router.get("/", response_model=List[TaskOut])
async def list_tasks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tasks = await task_service.list_tasks(db=db, skip=skip, limit=limit, parent_task_id=None)

    try:
        validated = [TaskOut.model_validate(t, from_attributes=True) for t in tasks]
        return validated
    except Exception as exc:
        logger.exception("Failed to serialize tasks list: %s", exc)
        if tasks:
            try:
                logger.debug("First task to serialize: %s", getattr(tasks[0], "to_dict", lambda: repr(tasks[0]))())
            except Exception:
                logger.debug("Could not inspect first task for debugging.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while serializing tasks")


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    try:
        return TaskOut.model_validate(task, from_attributes=True)
    except Exception as exc:
        logger.exception("Failed to serialize single task %s: %s", task_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while serializing task")


@router.patch("/{task_id}", response_model=TaskOut)
async def edit_task(
    task_id: int = Path(..., ge=1),
    payload: TaskUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Partially update a task. Provide only fields you want to change.
    Use 'parent_task_id' to change parent (reparenting checks apply).
    """
    patch = payload.model_dump(exclude_unset=True)

    try:
        updated = await task_service.update_task(db=db, task_id=task_id, patch=patch)
    except ValueError as exc:
        # validation errors from service (e.g. parent not found / cycle / wrong project)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    try:
        return TaskOut.model_validate(updated, from_attributes=True)
    except Exception as exc:
        logger.exception("Failed to serialize updated task %s: %s", task_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while serializing task")


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int = Path(..., ge=1),
    delete_subtasks: bool = Query(True),
    soft: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Delete a task. By default deletes the task and its descendant subtasks.
    Set delete_subtasks=false to reparent direct children to the deleted task's parent.
    Set soft=true to mark tasks as deleted if soft-delete is supported.
    """
    # Ensure the task exists and belongs to a project the user can act on (service raises if not)
    try:
        await task_service.delete_task(db=db, task_id=task_id, delete_subtasks=delete_subtasks, soft=soft)
    except ValueError as exc:
        # service raises for "not found" or unsupported soft delete
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{task_id}/subtasks", response_model=List[TaskOut])
async def list_subtasks(
    task_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    subtasks = await task_service.list_subtasks(db=db, parent_task_id=task_id)

    try:
        return [TaskOut.model_validate(t, from_attributes=True) for t in subtasks]
    except Exception as exc:
        logger.exception("Failed to serialize subtasks for parent id %s: %s", task_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while serializing subtasks")
