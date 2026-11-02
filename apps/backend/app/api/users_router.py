from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_schema import UserCreate, UserOut, UserUpdate, TokenOut
from app.schemas.task_schema import TaskOut
from app.core.database import get_db
from app.services.user_service import user_service
from app.services.task_service import task_service
from app.services.access import ADMIN, ensure_role
from app.api.dependencies import get_current_user
from app.models.user import User
from app.crud.user_repo import user_repo

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/tasks", response_model=List[TaskOut])
async def get_my_tasks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tasks assigned to the current user."""
    tasks = await task_service.list_tasks(
        db=db, skip=skip, limit=limit, assignee_id=current_user.id
    )
    return [TaskOut.model_validate(t, from_attributes=True) for t in tasks]


@router.get("/", response_model=List[UserOut])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_role(current_user, ADMIN)
    return await user_repo.list(db, skip=skip, limit=limit)


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_role(current_user, ADMIN)
    try:
        return await user_service.create_user(
            db=db,
            email=payload.email,
            password=payload.password,
            name=payload.name,
            phone=payload.phone,
            role=payload.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_role(current_user, ADMIN)
    try:
        return await user_service.update_user(db, user_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        code = status.HTTP_404_NOT_FOUND if str(exc) == "User not found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_role(current_user, ADMIN)
    try:
        await user_service.delete_user(db, user_id, current_user.id)
    except ValueError as exc:
        code = status.HTTP_404_NOT_FOUND if str(exc) == "User not found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc))


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db=Depends(get_db)):
    try:
        user = await user_service.create_user(
            db=db,
            email=payload.email,
            password=payload.password,
            name=payload.name,
            phone=payload.phone,
            role="member",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return user


@router.post("/login", response_model=TokenOut)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = await user_service.authenticate_user(db=db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = user_service.create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
