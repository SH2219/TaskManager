from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.project_repo import project_repo
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.task_assignment import TaskAssignment
from app.models.user import User
from app.services.access import ADMIN, LEAD


class ProjectService:
    """Service layer for Project operations."""

    async def create_project(
        self,
        db: AsyncSession,
        name: str,
        description: str | None = None
    ) -> Project:
        """Create a new project and commit to DB."""
        project = await project_repo.create(db, name=name, description=description)
        await db.commit()
        return await project_repo.get(db, project.id)

    async def get_project(self, db: AsyncSession, project_id: int) -> Project | None:
        """Get a project by ID."""
        return await project_repo.get(db, project_id)

    async def list_projects(
        self,
        db: AsyncSession,
        user: User,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """Admin sees every project. A project lead sees only assigned, active projects."""
        q = select(Project).options(selectinload(Project.members)).order_by(Project.id.desc())
        if user.role == ADMIN:
            if not include_archived:
                q = q.where(Project.archived_at.is_(None))
        elif user.role == LEAD:
            assigned = select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
            q = q.where(Project.id.in_(assigned), Project.archived_at.is_(None))
        else:
            return []
        q = q.offset(skip).limit(limit)
        return list((await db.execute(q)).scalars().unique().all())

    async def update_project(
        self,
        db: AsyncSession,
        project_id: int,
        patch: dict
    ) -> Project | None:
        """Update a project with given patch and commit."""
        allowed = {k: v for k, v in patch.items() if k in {"name", "description"}}
        project = await project_repo.update(db, project_id, allowed)
        if project:
            await db.commit()
            return await project_repo.get(db, project_id)
        return project

    async def set_archived(self, db: AsyncSession, project_id: int, archived: bool) -> Project | None:
        project = await project_repo.get(db, project_id)
        if not project:
            return None
        project.archived_at = datetime.now(timezone.utc) if archived else None
        db.add(project)
        await db.commit()
        return await project_repo.get(db, project_id)

    async def set_members(self, db: AsyncSession, project_id: int, user_ids: list[int]) -> Project | None:
        project = await project_repo.get(db, project_id)
        if not project:
            return None
        ids = list(dict.fromkeys(int(uid) for uid in user_ids))
        role_by_id: dict[int, str] = {}
        if ids:
            users = (await db.execute(select(User).where(User.id.in_(ids)))).scalars().all()
            role_by_id = {u.id: u.role or "member" for u in users}
            if set(role_by_id) != set(ids):
                raise ValueError("One or more users were not found")
        wanted = set(ids)
        for member in list(project.members or []):
            if member.user_id not in wanted:
                project.members.remove(member)
            else:
                member.role = role_by_id.get(member.user_id, member.role)
        have = {m.user_id for m in project.members}
        for uid in ids:
            if uid not in have:
                project.members.append(ProjectMember(user_id=uid, role=role_by_id.get(uid, "member")))
        await db.commit()
        return await project_repo.get(db, project_id)

    async def dashboard(self, db: AsyncSession, project_id: int) -> dict | None:
        project = await project_repo.get(db, project_id)
        if not project:
            return None
        tasks = (
            await db.execute(
                select(Task)
                .where(Task.project_id == project_id)
                .options(selectinload(Task.assignments).selectinload(TaskAssignment.user))
            )
        ).scalars().unique().all()
        scores: list[int] = []
        completed = 0
        for task in tasks:
            if task.status == "done":
                scores.append(100)
                completed += 1
                continue
            progresses = [a.progress or 0 for a in (task.assignments or [])]
            scores.append(round(sum(progresses) / len(progresses)) if progresses else 0)
        progress = round(sum(scores) / len(scores)) if scores else 0
        return {
            "project_id": project.id,
            "name": project.name,
            "description": project.description,
            "archived": bool(project.archived),
            "progress": progress,
            "task_count": len(tasks),
            "completed_count": completed,
            "open_count": len(tasks) - completed,
            "member_count": len(project.member_ids),
        }

    async def delete_project(self, db: AsyncSession, project_id: int) -> None:
        """Delete a project and commit."""
        await project_repo.delete(db, project_id)
        await db.commit()


project_service = ProjectService()
