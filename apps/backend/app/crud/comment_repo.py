# app/repositories/comment_repo.py
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment


class CommentRepo:
    async def get(self, db:AsyncSession, comment_id:int) -> Optional[Comment]:
        q= select(Comment).where(Comment.id==comment_id)
        result= await db.execute(q)
        return result.scalars().one_or_none()
    
    async def list_by_task(self, db:AsyncSession, task_id:int, skip:int=0, limit:int=100)-> list[Comment]:
        q= select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at).offset(skip).limit(limit)
        result= await db.execute(q)
        return result.scalars().all()
    
    async def create(self, db:AsyncSession,*, task_id:int, user_id:int | None=None, content:str)->Comment:
        comment = Comment(task_id=task_id, user_id=user_id, content=content)
        db.add(comment)
        await db.flush()
        await db.refresh(comment)   
        return comment
    
    async def update(self, db:AsyncSession, comment:Comment, patch:dict)->Comment:
        for k, v in patch.items():
            if hasattr(comment, k):
                setattr(comment, k, v)
                
        db.add(comment)
        await db.flush()
        await db.refresh(comment)
        return comment
    
    async def delete(self, db: AsyncSession, comment: Comment) -> None:
        await db.delete(comment)
        await db.flush()

comment_repo = CommentRepo()