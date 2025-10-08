# app/crud/tag_repo.py
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


class TagRepo:
    async def get(self, db: AsyncSession, tag_id: int) -> Optional[Tag]:
        q = select(Tag).where(Tag.id == tag_id)
        result = await db.execute(q)
        # correct API: use scalars().one_or_none() to retrieve an ORM object or None
        return result.scalars().one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Tag]:
        q = select(Tag).where(Tag.name == name)
        result = await db.execute(q)
        return result.scalars().one_or_none()

    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Tag]:
        q = select(Tag).offset(skip).limit(limit)
        result = await db.execute(q)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, name: str, color: str | None = None, description: str | None = None) -> Tag:
        tag = Tag(name=name, color=color, description=description)
        db.add(tag)
        await db.flush()
        await db.refresh(tag)
        return tag

    async def update(self, db: AsyncSession, tag: Tag, patch: dict) -> Tag:
        for k, v in patch.items():
            if hasattr(tag, k):
                setattr(tag, k, v)
        db.add(tag)
        await db.flush()
        await db.refresh(tag)
        return tag

    async def delete(self, db: AsyncSession, tag: Tag) -> None:
        await db.delete(tag)
        await db.flush()


tag_repo = TagRepo()
