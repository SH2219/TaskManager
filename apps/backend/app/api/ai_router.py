from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.schemas.ai_schema import GenerateTaskIn, GenerateTaskOut
from app.services.access import assert_project_access, ensure_role
from app.services.ai_service import ai_service
from app.services.project_service import project_service

router = APIRouter()


@router.post("/generate-task", response_model=GenerateTaskOut)
async def generate_task(
    payload: GenerateTaskIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_role(current_user, "admin", "project_lead")
    await assert_project_access(db, payload.project_id, current_user)

    project = await project_service.get_project(db, payload.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    members = (
        await db.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == payload.project_id)
            .options(selectinload(ProjectMember.user))
        )
    ).scalars().all()
    member_names = [
        (member.user.name or member.user.email)
        for member in members
        if member.user is not None
    ]

    tasks = (
        await db.execute(
            select(Task)
            .where(Task.project_id == payload.project_id)
            .order_by(Task.id.desc())
            .limit(30)
        )
    ).scalars().all()
    by_id = {task.id: task for task in tasks}
    existing_tasks = []
    for task in tasks:
        parent = by_id.get(task.parent_task_id) if task.parent_task_id else None
        existing_tasks.append(
            {
                "title": task.title,
                "status": task.status,
                "parent_title": parent.title if parent else None,
            }
        )

    parent_task_title = None
    if payload.parent_task_id:
        parent = by_id.get(payload.parent_task_id)
        if parent is None:
            parent = await db.get(Task, payload.parent_task_id)
        if parent is None or parent.project_id != payload.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent task must belong to this project",
            )
        parent_task_title = parent.title

    try:
        result = await ai_service.generate_task(
            payload.title,
            project_name=project.name,
            project_description=project.description,
            member_names=member_names,
            existing_tasks=existing_tasks,
            priority=payload.priority,
            due_at=payload.due_at,
            parent_task_title=parent_task_title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return result
