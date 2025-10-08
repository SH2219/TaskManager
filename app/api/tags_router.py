# app/api/tags_router.py
from typing import List, Dict
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.tag_schema import TagCreate, TagUpdate, TagRead
from app.services.tag_service import tag_service
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: TagCreate = Body(...), db:AsyncSession= Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create a new tag. (Requires authentication.)
    """
    
    try:
        tag = await tag_service.create_tag(db, name = payload.name, color= payload.color, description=payload.description)
        return TagRead.model_validate(tag, from_attributes=True)
    
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error(f"Unexpected error occurred: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    
@router.get("/tags/", response_model=List[TagRead])
async def list_tags(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    tags = await tag_service.list_tags(db=db, skip=skip, limit=limit)
    try:
        return [TagRead.model_validate(t, from_attributes=True) for t in tags]
    except Exception as exc:
        logger.exception("Failed to serialize tags list: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    
@router.patch("/tags/{tag_id}", response_model=TagRead)
async def update_tag(
    tag_id: int = Path(..., ge=1),
    payload: TagUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patch = payload.model_dump(exclude_unset=True)
    try:
        updated = await tag_service.update_tag(db=db, tag_id=tag_id, patch=patch)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    try:
        return TagRead.model_validate(updated, from_attributes=True)
    except Exception as exc:
        logger.exception("Failed to serialize updated tag %s: %s", tag_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    
@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        await tag_service.delete_tag(db=db, tag_id=tag_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error deleting tag %s: %s", tag_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    return None