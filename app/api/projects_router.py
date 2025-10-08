from fastapi import APIRouter, Depends, HTTPException, status,Body, Path, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.schemas.project_schema import ProjectCreate, ProjectOut
from app.services.project_service import project_service
from app.api.dependencies import get_current_user
import logging
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["Projects"])

# Create a new project
@router.post("/", response_model=ProjectOut)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await project_service.create_project(db, name=payload.name, description=payload.description)


# List all projects
@router.get("/", response_model=List[ProjectOut])
async def list_projects(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await project_service.list_projects(db, skip=skip, limit=limit)

# --- Edit project (partial update) ---
@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int = Path(..., ge=1),
    patch : dict = Body(...),
    db:AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Partially update a project. Provide only fields you want to change.
    Example body: {"name": "New name", "description": "New description"}
    """
    # Ensure project exists first
    existing_project = await project_service.get_project(db, project_id)
    if not existing_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    try:
        updated = await project_service.update_project(db, project_id, patch)
    except ValueError as exc:
        # If your service raises ValueError for validation issues
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    
    if not updated:
        # service returned None for some reason (treat as not found)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Explicitly convert ORM -> Pydantic for predictable serialization
    try:
        return ProjectOut.model_validate(updated, from_attributes=True)
    except Exception:
        logger.exception("Failed to serialize Project id=%s to ProjectOut", project_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while serializing project")

# --- Delete project ---
@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Delete a project. Returns 204 No Content on success.
    """
    # ensure project exists (and optionally enforce permissions here)
    existing = await project_service.get_project(db, project_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
     
    try:
        await project_service.delete_project(db, project_id)
    except ValueError as exc:
        # service may raise ValueError for constraints / validation
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    
    except Exception:
        logger.exception("Unexpected error while deleting project id=%s", project_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while deleting project")

    return Response(status_code=status.HTTP_204_NO_CONTENT)