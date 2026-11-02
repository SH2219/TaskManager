from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.notification_schema import NotificationOut
from app.services.notification_service import notification_service

router = APIRouter()


@router.get("/", response_model=List[NotificationOut])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await notification_service.list_for_user(db, current_user.id)


@router.post("/read-all", response_model=List[NotificationOut])
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await notification_service.mark_all_read(db, current_user.id)
    return await notification_service.list_for_user(db, current_user.id)


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = await notification_service.mark_read(db, notification_id, current_user.id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return row
