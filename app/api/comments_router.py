# app/api/comments_router.py
from typing import List, Dict
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.comment_schema import CommentCreate, CommentUpdate, CommentRead
from app.services.comment_service import comment_service
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/tasks/{task_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(
    task_id: int = Path(..., ge=1),
    payload: CommentCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create a comment on a task. The task_id in path must match payload.task_id (for safety).
    """
    if payload.task_id != task_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task_id in path and body must match")

    try:
        comment = await comment_service.create_comment(db=db, creator_user_id=current_user.id, task_id=task_id, content=payload.content)
        return CommentRead.model_validate(comment, from_attributes=True)
    except ValueError as exc:
        # e.g., task not found
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error creating comment for task %s: %s", task_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    
    
@router.get("/tasks/{task_id}/comments", response_model=List[CommentRead])
async def list_comments(
    task_id: int = Path(..., ge=1),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    comments = await comment_service.list_comments_for_task(db=db, task_id=task_id, skip=skip, limit=limit)
    try:
        return [CommentRead.model_validate(c, from_attributes=True) for c in comments]
    except Exception as exc:
        logger.exception("Failed to serialize comments for task %s: %s", task_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.patch("/comments/{comment_id}", response_model=CommentRead)
async def update_comment(
    comment_id: int = Path(..., ge=1),
    payload: CommentUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patch = payload.model_dump(exclude_unset=True)
    try:
        updated = await comment_service.update_comment(db=db, comment_id=comment_id, patch=patch, requester_user_id=current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error updating comment %s: %s", comment_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    try:
        return CommentRead.model_validate(updated, from_attributes=True)
    except Exception as exc:
        logger.exception("Failed to serialize updated comment %s: %s", comment_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        await comment_service.delete_comment(db=db, comment_id=comment_id, requester_user_id=current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error deleting comment %s: %s", comment_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    return None