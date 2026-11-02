from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User

ADMIN = "admin"
LEAD = "project_lead"
MEMBER = "member"
ROLES = (ADMIN, LEAD, MEMBER)


def ensure_role(user: User, *roles: str) -> None:
    if user.role not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this action",
        )


async def member_project_ids(db: AsyncSession, user_id: int) -> set[int]:
    rows = (
        await db.execute(
            select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
        )
    ).scalars().all()
    return set(rows)


async def assert_project_access(db: AsyncSession, project_id: int, user: User) -> None:
    """Admin sees every project. A project lead only sees projects they belong to."""
    if user.role == ADMIN:
        return
    if user.role == LEAD and project_id in await member_project_ids(db, user.id):
        project = await db.get(Project, project_id)
        if project is not None and project.archived_at is None:
            return
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This project is not assigned to you",
    )


async def assert_task_view(db: AsyncSession, task, user: User) -> None:
    if user.role == ADMIN:
        return
    if user.role == LEAD and task.project_id in await member_project_ids(db, user.id):
        return
    if any(a.user_id == user.id for a in (task.assignments or [])):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This task is not assigned to you",
    )
