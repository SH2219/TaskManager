# app/services/comment_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict

from app.crud.comment_repo import comment_repo
from app.crud.task_repo import task_repo   # ensure this exists at that path
from app.models.comment import Comment


class CommentService:
    async def create_comment(self, db: AsyncSession, creator_user_id: int, *, task_id: int, content: str) -> Comment:
        # Validation: task must exist
        task = await task_repo.get(db, task_id)
        if not task:
            raise ValueError(f"Task not found (id={task_id})")
        
        comment = await comment_repo.create(db, task_id=task_id, user_id=creator_user_id, content=content)
        await db.commit()
        await db.refresh(comment)
        return comment
    
    async def get_comment(self, db: AsyncSession, comment_id: int) -> Optional[Comment]:
        return await comment_repo.get(db, comment_id)
    
    async def list_comments_for_task(self, db: AsyncSession, task_id: int, skip: int = 0, limit: int = 100) -> List[Comment]:
        return await comment_repo.list_by_task(db, task_id, skip=skip, limit=limit)
    
    async def update_comment(self, db: AsyncSession, comment_id: int, patch: Dict, requester_user_id: int) -> Optional[Comment]:
        comment = await comment_repo.get(db, comment_id)
        if not comment:
            return None

        # Only author allowed to update (modify as per your permission model)
        if comment.user_id is not None and comment.user_id != requester_user_id:
            raise PermissionError("Not allowed to edit this comment")

        comment = await comment_repo.update(db, comment, patch)
        await db.commit()
        await db.refresh(comment)
        return comment
    
    async def delete_comment(self, db: AsyncSession, comment_id: int, requester_user_id: int) -> None:
        comment = await comment_repo.get(db, comment_id)
        if not comment:
            raise ValueError("Comment not found")

        if comment.user_id is not None and comment.user_id != requester_user_id:
            raise PermissionError("Not allowed to delete this comment")

        await comment_repo.delete(db, comment)
        await db.commit()

comment_service = CommentService()