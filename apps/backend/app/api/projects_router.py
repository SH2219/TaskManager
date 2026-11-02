from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.schemas.project_schema import ProjectCreate, ProjectDashboardOut, ProjectMembersBody, ProjectOut, ProjectUpdate
from app.services.project_service import project_service
from app.services.access import ADMIN, LEAD, ensure_role, assert_project_access
from app.api.dependencies import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ensure_role(user, ADMIN)
    return await project_service.create_project(db, name=payload.name, description=payload.description)


@router.get("/", response_model=List[ProjectOut])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await project_service.list_projects(
        db,
        user,
        include_archived=include_archived and user.role == ADMIN,
        skip=skip,
        limit=limit,
    )


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await assert_project_access(db, project_id, user)
    project = await project_service.get_project(db, project_id)
    if not project or (user.role == LEAD and project.archived):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/{project_id}/dashboard", response_model=ProjectDashboardOut)
async def project_dashboard(
    project_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await assert_project_access(db, project_id, user)
    data = await project_service.dashboard(db, project_id)
    if not data or (user.role == LEAD and data["archived"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return data


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int = Path(..., ge=1),
    payload: ProjectUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ensure_role(user, ADMIN)
    existing_project = await project_service.get_project(db, project_id)
    if not existing_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    try:
        updated = await project_service.update_project(db, project_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectOut.model_validate(updated, from_attributes=True)


@router.put("/{project_id}/members", response_model=ProjectOut)
async def set_project_members(
    project_id: int = Path(..., ge=1),
    payload: ProjectMembersBody = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ensure_role(user, ADMIN)
    try:
        updated = await project_service.set_members(db, project_id, payload.user_ids)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectOut.model_validate(updated, from_attributes=True)


@router.post("/{project_id}/archive", response_model=ProjectOut)
async def archive_project(
    project_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ensure_role(user, ADMIN)
    updated = await project_service.set_archived(db, project_id, True)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return updated


@router.post("/{project_id}/restore", response_model=ProjectOut)
async def restore_project(
    project_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ensure_role(user, ADMIN)
    updated = await project_service.set_archived(db, project_id, False)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return updated


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ensure_role(user, ADMIN)
    existing = await project_service.get_project(db, project_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    try:
        await project_service.delete_project(db, project_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        logger.exception("Unexpected error while deleting project id=%s", project_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while deleting project")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
