from typing import List
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Body, status, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.task_schema import TaskCreate, TaskUpdate, TaskOut
from app.schemas.assignment_schema import AssignUsersBody, TaskAssignmentOut, TaskAssignmentUpdate
from app.services.task_service import task_service
from app.services.access import ADMIN, LEAD, MEMBER, ensure_role, assert_project_access, assert_task_view, member_project_ids
from app.api.dependencies import get_current_user
from app.models.project import Project
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

LEAD_STATUS = {"todo", "in_progress"}


def _out(task):
    return TaskOut.model_validate(task, from_attributes=True)


@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_role(current_user, ADMIN)
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
            status=payload.status,
            priority=payload.priority,
            due_at=payload.due_at,
            start_at=payload.start_at,
            estimated_minutes=payload.estimated_minutes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _out(task)


@router.get("/", response_model=List[TaskOut])
async def list_tasks(
    skip: int = 0,
    limit: int = 100,
    project_id: int | None = Query(None, ge=1),
    top_level_only: bool = Query(False),
    assignee_id: int | None = Query(None, ge=1),
    mine: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_ids = None
    user_filter = current_user.id if mine else assignee_id
    if current_user.role == MEMBER:
        user_filter = current_user.id
    elif current_user.role == LEAD:
        assigned = await member_project_ids(db, current_user.id)
        if not assigned:
            project_ids = set()
        else:
            active = (
                await db.execute(
                    select(Project.id).where(
                        Project.id.in_(assigned),
                        Project.archived_at.is_(None),
                    )
                )
            ).scalars().all()
            project_ids = set(active)
        if project_id is not None and project_id not in project_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This project is not assigned to you")
    elif current_user.role != ADMIN:
        ensure_role(current_user, ADMIN)

    tasks = await task_service.list_tasks(
        db=db,
        skip=skip,
        limit=limit,
        project_id=project_id,
        top_level_only=top_level_only,
        assignee_id=user_filter,
        project_ids=project_ids,
    )
    return [_out(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await assert_task_view(db, task, current_user)
    return _out(task)


@router.patch("/{task_id}", response_model=TaskOut)
async def edit_task(
    task_id: int = Path(..., ge=1),
    payload: TaskUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patch = payload.model_dump(exclude_unset=True)
    existing = await task_service.get_task(db, task_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if current_user.role == LEAD:
        await assert_project_access(db, existing.project_id, current_user)
        extra = set(patch) - {"status"}
        if extra:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Project leads update status here. Completion is a separate step.",
            )
        if "status" in patch and patch["status"] not in LEAD_STATUS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Choose to do or in progress. Mark the task completed when the work is finished.",
            )
    else:
        ensure_role(current_user, ADMIN)

    try:
        updated = await task_service.update_task(db=db, task_id=task_id, patch=patch, actor_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return _out(updated)


@router.post("/{task_id}/complete", response_model=TaskOut)
async def complete_task(
    task_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await task_service.get_task(db, task_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if current_user.role == LEAD:
        await assert_project_access(db, existing.project_id, current_user)
    else:
        ensure_role(current_user, ADMIN)
    updated = await task_service.mark_complete(db, task_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return _out(updated)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int = Path(..., ge=1),
    delete_subtasks: bool = Query(True),
    soft: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_role(current_user, ADMIN)
    try:
        await task_service.delete_task(db=db, task_id=task_id, delete_subtasks=delete_subtasks, soft=soft)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{task_id}/subtasks", response_model=List[TaskOut])
async def list_subtasks(
    task_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parent = await task_service.get_task(db, task_id)
    if not parent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await assert_task_view(db, parent, current_user)
    subtasks = await task_service.list_subtasks(db=db, parent_task_id=task_id)
    return [_out(t) for t in subtasks]


@router.put("/{task_id}/assignments", response_model=TaskOut)
async def set_task_assignments(
    task_id: int = Path(..., ge=1),
    payload: AssignUsersBody = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_role(current_user, ADMIN)
    try:
        task = await task_service.assign_users(db, task_id, payload.user_ids, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return _out(task)


@router.patch("/{task_id}/assignments/{user_id}", response_model=TaskAssignmentOut)
async def update_task_assignment(
    task_id: int = Path(..., ge=1),
    user_id: int = Path(..., ge=1),
    payload: TaskAssignmentUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if current_user.role == LEAD:
        await assert_project_access(db, task.project_id, current_user)
    else:
        ensure_role(current_user, ADMIN)
    try:
        assignment = await task_service.update_assignment(
            db,
            task_id,
            user_id,
            progress=payload.progress,
            rating=payload.rating,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return TaskAssignmentOut.model_validate(assignment, from_attributes=True)
