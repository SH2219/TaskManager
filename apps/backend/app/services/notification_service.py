from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationService:
    async def notify_task_assigned(
        self,
        db: AsyncSession,
        *,
        user_ids: list[int],
        actor_id: int,
        actor_name: str,
        task_id: int,
        project_id: int,
        task_title: str,
    ) -> None:
        for uid in user_ids:
            if uid == actor_id:
                continue
            db.add(
                Notification(
                    user_id=uid,
                    kind="task_assigned",
                    title="Task assigned",
                    body=f'{actor_name} assigned you "{task_title}".',
                    task_id=task_id,
                    project_id=project_id,
                )
            )

    async def list_for_user(self, db: AsyncSession, user_id: int, limit: int = 30) -> list[Notification]:
        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_read(self, db: AsyncSession, notification_id: int, user_id: int) -> Notification | None:
        row = (
            await db.execute(
                select(Notification).where(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        if row.read_at is None:
            row.read_at = datetime.now(timezone.utc)
            db.add(row)
            await db.commit()
            await db.refresh(row)
        return row

    async def mark_all_read(self, db: AsyncSession, user_id: int) -> None:
        await db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .values(read_at=datetime.now(timezone.utc))
        )
        await db.commit()


notification_service = NotificationService()
