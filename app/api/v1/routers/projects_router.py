from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.schemas.project_schema import ProjectCreate, ProjectOut
from app.services.project_service import project_service
from app.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])

# Create a new project
@router.post("/", response_model=ProjectOut)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await project_service.create_project(db, name=payload.name, description=payload.description)


# List all projects
@router.get("/", response_model=List[ProjectOut])
async def list_projects(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await project_service.list_projects(db, skip=skip, limit=limit)
