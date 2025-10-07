# app/services/task_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Iterable, List, Optional, Dict, Set
from app.models.user import User
from sqlalchemy.orm import selectinload
from app.models.task import Task

class TaskService:
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
        due_at = None,
        start_at = None,
        estimated_minutes: Optional[int] = None,
    ) -> Task:
        """
        Create a task; parent_task_id is optional.
        If provided and >0, parent must exist and belong to same project.
        """

        # Normalize parent id: treat falsy / invalid as None
        if parent_task_id is not None:
            try:
                parent_task_id = int(parent_task_id)
            except (TypeError, ValueError):
                parent_task_id = None

            if parent_task_id is not None and parent_task_id <= 0:
                parent_task_id = None

        # Validate parent (only if provided and positive)
        if parent_task_id is not None:
            parent = (await db.execute(select(Task).where(Task.id == parent_task_id))).scalar_one_or_none()
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
            priority=priority,
            due_at=due_at,
            start_at=start_at,
            estimated_minutes=estimated_minutes,
        )

        if assignee_ids:
            users = (await db.execute(select(User).where(User.id.in_(set(assignee_ids))))).scalars().all()
            new_task.assignees = users

        db.add(new_task)
        await db.flush()
        await db.commit()

        # Re-query with eager loads so returned Task has relationships populated
        q = select(Task).where(Task.id == new_task.id).options(
            selectinload(Task.assignees),
            selectinload(Task.subtasks)  # optional; needed if your schema reads subtasks
        )
        result = await db.execute(q)
        task = result.scalar_one()
        return task

    async def get_task(self, db: AsyncSession, task_id: int) -> Optional[Task]:
        q = select(Task).where(Task.id == task_id).options(selectinload(Task.assignees))
        result = await db.execute(q)
        return result.scalar_one_or_none()

    async def list_tasks(self, db: AsyncSession, skip: int = 0, limit: int = 100, parent_task_id: Optional[int] = None) -> List[Task]:
        q = select(Task).offset(skip).limit(limit).options(selectinload(Task.assignees))
        if parent_task_id is not None:
            q = q.where(Task.parent_task_id == parent_task_id)
        return (await db.execute(q)).scalars().all()

    async def list_subtasks(self, db: AsyncSession, parent_task_id: int, skip:int=0, limit:int=100) -> List[Task]:
        # convenience wrapper
        return await self.list_tasks(db=db, skip=skip, limit=limit, parent_task_id=parent_task_id)

    async def update_task(self, db: AsyncSession, task_id: int, patch: Dict) -> Optional[Task]:
        task = await self.get_task(db, task_id)
        if not task:
            return None

        if "parent_task_id" in patch:
            new_parent_id = patch.pop("parent_task_id")
            await self.reparent_task(db, task_id, new_parent_id)
            task = await self.get_task(db, task_id)

        if "assignee_ids" in patch:
            ids = patch.pop("assignee_ids") or []
            users = (await db.execute(select(User).where(User.id.in_(set(ids))))).scalars().all()
            task.assignees = users

        for key, val in patch.items():
            if hasattr(task, key):
                setattr(task, key, val)

        db.add(task)
        await db.commit()

        # re-query eagerly to ensure relationships are loaded
        q = select(Task).where(Task.id == task.id).options(selectinload(Task.assignees), selectinload(Task.subtasks))
        result = await db.execute(q)
        return result.scalar_one_or_none()

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

            # detect cycle
            cur = parent
            while cur:
                if cur.id == task.id:
                    raise ValueError("Reparenting would create a cycle")
                cur = await self.get_task(db, cur.parent_task_id) if cur.parent_task_id else None

            task.parent_task_id = new_parent_id_int

        db.add(task)
        await db.commit()

        # re-query with eager loads
        q = select(Task).where(Task.id == task.id).options(selectinload(Task.assignees), selectinload(Task.subtasks))
        result = await db.execute(q)
        return result.scalar_one()

    async def assign_users(self, db: AsyncSession, task_id: int, user_ids: Iterable[int]) -> Optional[Task]:
        task = await self.get_task(db, task_id)
        if not task:
            return None
        users = (await db.execute(select(User).where(User.id.in_(set(user_ids))))).scalars().all()
        task.assignees = users
        db.add(task)
        await db.commit()

        # re-query with eager loads
        q = select(Task).where(Task.id == task.id).options(selectinload(Task.assignees), selectinload(Task.subtasks))
        result = await db.execute(q)
        return result.scalar_one_or_none()

    async def delete_task(self, db: AsyncSession, task_id: int, delete_subtasks: bool = True, soft: bool = False) -> None:
        root = await self.get_task(db, task_id)
        if not root:
            raise ValueError("Task not found")

        # load all tasks in same project
        q = select(Task).where(Task.project_id == root.project_id).options(selectinload(Task.assignees))
        all_tasks = (await db.execute(q)).scalars().all()

        children_map = {}
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
        else:
            direct_children = children_map.get(root.id, [])
            for child in direct_children:
                child.parent_task_id = root.parent_task_id
                db.add(child)
            await db.execute(delete(Task).where(Task.id == root.id))
            await db.commit()
            return

task_service = TaskService()
