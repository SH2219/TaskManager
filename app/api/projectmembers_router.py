# app/api/projectmembers_router.py
from typing import List
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Body, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.projectmember_schema import ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberRead
from app.services.projectmembers_service import projectmembers_service
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/projects/{project_id}/members", response_model=ProjectMemberRead, status_code=status.HTTP_201_CREATED)
async def add_member(
    project_id: int = Path(..., ge=1),
    payload: ProjectMemberCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id in path and body must match")
    try:
        pm = await projectmembers_service.create_membership(
            db=db,
            requester_user=current_user,
            project_id=project_id,
            user_id=payload.user_id,
            role=payload.role,
        )
        return ProjectMemberRead.model_validate(pm, from_attributes=True)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error adding member: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/projects/{project_id}/members", response_model=List[ProjectMemberRead])
async def list_members(
    project_id: int = Path(..., ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        members = await projectmembers_service.list_members(db=db, project_id=project_id, skip=skip, limit=limit)
        return [ProjectMemberRead.model_validate(m, from_attributes=True) for m in members]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error listing members: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.patch("/projects/members/{membership_id}", response_model=ProjectMemberRead)
async def update_member(
    membership_id: int = Path(..., ge=1),
    payload: ProjectMemberUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patch = payload.model_dump(exclude_unset=True)
    try:
        updated = await projectmembers_service.update_membership(
            db=db,
            requester_user=current_user,
            membership_id=membership_id,
            patch=patch,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error updating membership: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

    return ProjectMemberRead.model_validate(updated, from_attributes=True)


@router.delete("/projects/members/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    membership_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        await projectmembers_service.delete_membership(db=db, requester_user=current_user, membership_id=membership_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        # membership not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error deleting membership: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    # 204 No Content — returning None is correct
    return None
