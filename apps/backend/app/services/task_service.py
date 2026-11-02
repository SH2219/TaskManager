# app/services/task_service.py
from typing import Dict, Iterable, List, Optional, Set

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.task_assignment import TaskAssignment
from app.models.user import User
from app.services.notification_service import notification_service


def _task_options():
    return (
        selectinload(Task.assignments).selectinload(TaskAssignment.user),
        selectinload(Task.tags),
        selectinload(Task.comments),
        selectinload(Task.project),
    )


class TaskService:
    async def _reload(self, db: AsyncSession, task_id: int) -> Optional[Task]:
        q = select(Task).where(Task.id == task_id).options(*_task_options())
        return (await db.execute(q)).scalar_one_or_none()

    async def _replace_assignments(
        self,
        db: AsyncSession,
        task: Task,
        user_ids: Iterable[int],
    ) -> list[int]:
        ids = list(dict.fromkeys(int(uid) for uid in user_ids))
        if ids:
            members = (
                await db.execute(
                    select(ProjectMember.user_id).where(
                        ProjectMember.project_id == task.project_id,
                        ProjectMember.user_id.in_(ids),
                    )
                )
            ).scalars().all()
            if set(members) != set(ids):
                raise ValueError("Assignees must be members of this project")

        wanted = set(ids)
        for assignment in list(task.assignments or []):
            if assignment.user_id not in wanted:
                task.assignments.remove(assignment)
        have = {a.user_id for a in task.assignments}
        added: list[int] = []
        for uid in ids:
            if uid not in have:
                task.assignments.append(TaskAssignment(user_id=uid, progress=0))
                added.append(uid)
        return added

    async def _notify_assignees(self, db: AsyncSession, task: Task, user_ids: list[int], actor_id: int) -> None:
        if not user_ids:
            return
        actor = await db.get(User, actor_id)
        actor_name = (actor.name or actor.email) if actor else "Someone"
        await notification_service.notify_task_assigned(
            db,
            user_ids=user_ids,
            actor_id=actor_id,
            actor_name=actor_name,
            task_id=task.id,
            project_id=task.project_id,
            task_title=task.title,
        )

    async def create_task(
        self,
        db: AsyncSession,
        creator_id: int,
        title: str,
        project_id: int,
        parent_task_id: Optional[int] = None,
        assignee_ids: Optional[Iterable[int]] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        status: Optional[str] = None,
        due_at=None,
        start_at=None,
        estimated_minutes: Optional[int] = None,
    ) -> Task:
        if parent_task_id is not None:
            try:
                parent_task_id = int(parent_task_id)
            except (TypeError, ValueError):
                parent_task_id = None
            if parent_task_id is not None and parent_task_id <= 0:
                parent_task_id = None

        if parent_task_id is not None:
            parent = (
                await db.execute(select(Task).where(Task.id == parent_task_id))
            ).scalar_one_or_none()
            if parent is None:
                raise ValueError(f"Parent task not found (id={parent_task_id})")
            if parent.project_id != project_id:
                raise ValueError("Parent task must belong to the same project")

        new_task = Task(
            title=title,
            description=description,
            project_id=project_id,
            creator_id=creator_id,
            parent_task_id=parent_task_id,
            priority=priority if priority is not None else 3,
            status=status or "todo",
            due_at=due_at,
            start_at=start_at,
            estimated_minutes=estimated_minutes,
        )
        db.add(new_task)
        await db.flush()
        added: list[int] = []
        if assignee_ids:
            await db.refresh(new_task, attribute_names=["assignments"])
            added = await self._replace_assignments(db, new_task, assignee_ids)
        await self._notify_assignees(db, new_task, added, creator_id)
        await db.commit()
        task = await self._reload(db, new_task.id)
        if task is None:
            raise ValueError("Task was not created")
        return task

    async def get_task(self, db: AsyncSession, task_id: int) -> Optional[Task]:
        return await self._reload(db, task_id)

    async def list_tasks(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        parent_task_id: Optional[int] = None,
        project_id: Optional[int] = None,
        top_level_only: bool = False,
        assignee_id: Optional[int] = None,
        project_ids: Optional[Iterable[int]] = None,
    ) -> List[Task]:
        q = select(Task).options(*_task_options())
        if project_ids is not None:
            allowed = list(project_ids)
            if not allowed:
                return []
            q = q.where(Task.project_id.in_(allowed))
        if project_id is not None:
            q = q.where(Task.project_id == project_id)
        if top_level_only:
            q = q.where(Task.parent_task_id.is_(None))
        elif parent_task_id is not None:
            q = q.where(Task.parent_task_id == parent_task_id)
        if assignee_id is not None:
            q = q.join(Task.assignments).where(TaskAssignment.user_id == assignee_id)
        q = q.order_by(Task.id.desc()).offset(skip).limit(limit)
        return list((await db.execute(q)).scalars().unique().all())

    async def list_subtasks(
        self,
        db: AsyncSession,
        parent_task_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        return await self.list_tasks(
            db=db, skip=skip, limit=limit, parent_task_id=parent_task_id
        )

    async def update_task(
        self,
        db: AsyncSession,
        task_id: int,
        patch: Dict,
        actor_id: Optional[int] = None,
    ) -> Optional[Task]:
        task = await self.get_task(db, task_id)
        if not task:
            return None

        if "parent_task_id" in patch:
            new_parent_id = patch.pop("parent_task_id")
            await self.reparent_task(db, task_id, new_parent_id)
            task = await self.get_task(db, task_id)
            if not task:
                return None

        added: list[int] = []
        if "assignee_ids" in patch:
            ids = patch.pop("assignee_ids") or []
            added = await self._replace_assignments(db, task, ids)
            if actor_id is not None:
                await self._notify_assignees(db, task, added, actor_id)

        for key, val in patch.items():
            if hasattr(task, key) and key not in {"assignments", "id"}:
                setattr(task, key, val)

        db.add(task)
        await db.commit()
        return await self._reload(db, task.id)

    async def reparent_task(self, db: AsyncSession, task_id: int, new_parent_id: Optional[int]) -> Task:
        task = await self.get_task(db, task_id)
        if not task:
            raise ValueError("Task not found")

        if new_parent_id is None:
            task.parent_task_id = None
        else:
            try:
                new_parent_id_int = int(new_parent_id)
            except (TypeError, ValueError):
                raise ValueError("Invalid parent id")

            parent = await self.get_task(db, new_parent_id_int)
            if not parent:
                raise ValueError("Parent not found")
            if parent.project_id != task.project_id:
                raise ValueError("Parent must be in the same project")

            cur = parent
            while cur:
                if cur.id == task.id:
                    raise ValueError("Reparenting would create a cycle")
                cur = await self.get_task(db, cur.parent_task_id) if cur.parent_task_id else None

            task.parent_task_id = new_parent_id_int

        db.add(task)
        await db.commit()
        reloaded = await self._reload(db, task.id)
        if reloaded is None:
            raise ValueError("Task not found")
        return reloaded

    async def assign_users(
        self,
        db: AsyncSession,
        task_id: int,
        user_ids: Iterable[int],
        actor_id: int,
    ) -> Optional[Task]:
        task = await self.get_task(db, task_id)
        if not task:
            return None
        added = await self._replace_assignments(db, task, user_ids)
        await self._notify_assignees(db, task, added, actor_id)
        db.add(task)
        await db.commit()
        return await self._reload(db, task.id)

    async def update_assignment(
        self,
        db: AsyncSession,
        task_id: int,
        user_id: int,
        progress: Optional[int] = None,
        rating: Optional[int] = None,
    ) -> TaskAssignment:
        q = (
            select(TaskAssignment)
            .where(TaskAssignment.task_id == task_id, TaskAssignment.user_id == user_id)
            .options(selectinload(TaskAssignment.user))
        )
        assignment = (await db.execute(q)).scalar_one_or_none()
        if assignment is None:
            raise ValueError("Assignment not found")
        if progress is not None:
            assignment.progress = progress
        if rating is not None:
            assignment.rating = rating
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        reloaded = (await db.execute(q)).scalar_one()
        return reloaded

    async def mark_complete(self, db: AsyncSession, task_id: int) -> Optional[Task]:
        task = await self.get_task(db, task_id)
        if not task:
            return None
        task.status = "done"
        for assignment in task.assignments or []:
            assignment.progress = 100
            db.add(assignment)
        db.add(task)
        await db.commit()
        return await self._reload(db, task_id)

    async def delete_task(
        self,
        db: AsyncSession,
        task_id: int,
        delete_subtasks: bool = True,
        soft: bool = False,
    ) -> None:
        root = await self.get_task(db, task_id)
        if not root:
            raise ValueError("Task not found")

        q = select(Task).where(Task.project_id == root.project_id)
        all_tasks = (await db.execute(q)).scalars().all()

        children_map: Dict[Optional[int], List[Task]] = {}
        for t in all_tasks:
            children_map.setdefault(t.parent_task_id, []).append(t)

        descendants: Set[int] = set()

        def collect(node_id: int):
            descendants.add(node_id)
            for child in children_map.get(node_id, []):
                collect(child.id)

        collect(root.id)

        supports_soft = hasattr(Task, "is_deleted")
        if soft and supports_soft:
            for t in (await db.execute(select(Task).where(Task.id.in_(descendants)))).scalars().all():
                setattr(t, "is_deleted", True)
                db.add(t)
            await db.commit()
            return
        if soft and not supports_soft:
            raise ValueError("Soft delete requested but Task model has no 'is_deleted' attribute")

        if delete_subtasks:
            await db.execute(delete(Task).where(Task.id.in_(descendants)))
            await db.commit()
            return

        direct_children = children_map.get(root.id, [])
        for child in direct_children:
            child.parent_task_id = root.parent_task_id
            db.add(child)
        await db.execute(delete(Task).where(Task.id == root.id))
        await db.commit()


task_service = TaskService()
