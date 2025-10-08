# app/services/tag_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict

from app.crud.tag_repo import tag_repo
from app.models.tag import Tag

class TagService:
    async def create_tag(self, db:AsyncSession, *, name : str, color:Optional[str]=None, description:Optional[str]=None)->Tag:
        # Validation: name must be unique (case-sensitive here; adjust if you want case-insensitive)
        existing = await tag_repo.get_by_name(db, name)
        if existing:
            raise ValueError(f"Tag with name {name!r} already exists.")
        tag = await tag_repo.create(db, name=name, color=color, description=description)
        await db.commit()
        await db.refresh(tag)
        return tag
    
    async def get_tag(self, db:AsyncSession, tag_id:int)->Optional[Tag]:
        return await tag_repo.get(db, tag_id)
    
    async def list_tags(self, db :AsyncSession,skip:int=0, limit:int=100)->List[Tag]:
        return await tag_repo.list(db, skip=skip, limit=limit)
    
    async def update_tag(self, db:AsyncSession, tag_id:int, patch:Dict)->Tag:
        tag = await tag_repo.get(db, tag_id)
        if not tag:
            raise ValueError(f"Tag with id {tag_id} not found.")
        
        # If updating name, ensure uniqueness
        new_name = patch.get("name")
        if new_name and new_name != tag.name:
            existing = await tag_repo.get_by_name(db, new_name)
            if existing:
                raise ValueError(f"Tag with name {new_name!r} already exists.")
        
        tag = await tag_repo.update(db, tag, patch)
        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        return tag
    
    async def delete_tag(self, db: AsyncSession, tag_id: int) -> None:
        tag = await tag_repo.get(db, tag_id)
        if not tag:
            raise ValueError("Tag not found")
        # Optional: prevent deletion if tag is in use. For simplicity, allow delete (cascade will remove associations).
        await tag_repo.delete(db, tag)
        await db.commit()

tag_service = TagService()