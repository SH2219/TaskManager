# app/api/progress_router.py
from typing import List, Dict, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Body, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.progress_schema import ProgressCreate, ProgressUpdate as ProgressUpdateSchema, ProgressRead
from app.services.progress_service import progress_service
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/tasks/{task_id}/progress", response_model=ProgressRead, status_code=status.HTTP_201_CREATED)
async def create_progress(
    task_id: int = Path(..., ge=1),
    payload: ProgressCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # path/body sanity check
    if payload.task_id != task_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task_id in path and body must match")

    try:
        pu = await progress_service.create_progress(db=db, creator_user_id=current_user.id, task_id=task_id, value=payload.value, note=payload.note)
        return ProgressRead.model_validate(pu, from_attributes=True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error creating progress for task %s: %s", task_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/tasks/{task_id}/progress", response_model=List[ProgressRead])
async def list_progress(
    task_id: int = Path(..., ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    pus = await progress_service.list_progress_for_task(db=db, task_id=task_id, skip=skip, limit=limit)
    try:
        return [ProgressRead.model_validate(p, from_attributes=True) for p in pus]
    except Exception as exc:
        logger.exception("Failed to serialize progress list for task %s: %s", task_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.patch("/progress/{progress_id}", response_model=ProgressRead)
async def update_progress(
    progress_id: int = Path(..., ge=1),
    payload: ProgressUpdateSchema = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patch = payload.model_dump(exclude_unset=True)
    try:
        updated = await progress_service.update_progress(db=db, progress_id=progress_id, patch=patch, requester_user_id=current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error updating progress %s: %s", progress_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress update not found")

    try:
        return ProgressRead.model_validate(updated, from_attributes=True)
    except Exception as exc:
        logger.exception("Failed to serialize updated progress %s: %s", progress_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/progress/{progress_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_progress(
    progress_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        await progress_service.delete_progress(db=db, progress_id=progress_id, requester_user_id=current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error deleting progress %s: %s", progress_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    return None
