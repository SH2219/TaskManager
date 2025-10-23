# app/api/v1/routers/users_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional
# app/api/v1/routers/users_router.py (fixed)
from app.schemas.user_schema import UserCreate, UserOut, TokenOut
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import user_service
from app.api.dependencies import get_db  # your DB dependency
from app.schemas.user_schema import UserCreate, UserOut, TokenOut, UserUpdate
from app.api.dependencies import get_db, get_current_user
from app.models.user import User as UserModel  # ORM model type annotation (if needed)


logger = logging.getLogger(__name__)
router = APIRouter()  # <--- NO prefix here

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db=Depends(get_db)):
    user = await user_service.create_user(db=db, email=payload.email, password=payload.password, name=payload.name)
    print("Created user:", user.id)
    return user

@router.post("/login", response_model=TokenOut)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    # OAuth2 form uses 'username' for email
    user = await user_service.authenticate_user(db=db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
      # create_access_token is synchronous
    token = user_service.create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
  
  
  # --- User list / search (admin in future) ---------------------------------
@router.get("/", response_model=List[UserOut])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    List users (paginated). IMPORTANT: currently any authenticated user can call this;
    in production you should restrict this endpoint to admin users only.
    """
    # TODO: enforce admin-only access here when you add roles
    users = await user_service.list_users(db=db, skip=skip, limit=limit)
    return [UserOut.model_validate(u, from_attributes=True) for u in users]


@router.get("/search", response_model=List[UserOut])
async def search_users(
    email: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Search users by email and/or name. At least one query param must be provided.
    Returns a list (maybe empty). TODO: make admin-only if required.
    """
    if not email and not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide at least one search parameter: email or name")

    users = await user_service.search_users(db=db, email=email, name=name, skip=skip, limit=limit)
    return [UserOut.model_validate(u, from_attributes=True) for u in users]


# --- Get single user (owner only for now) ---------------------------------
@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get a single user by id. Current behaviour: only the user themself can fetch their record.
    Later: allow admins to fetch other users.
    """
    # owner-only check
    if current_user.id != user_id:
        # TODO: if you add admin role, allow admins here
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this user")

    user = await user_service.get_user(db=db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut.model_validate(user, from_attributes=True)


# --- Patch / Update user (owner only) ------------------------------------
@router.patch("/{user_id}", response_model=UserOut)
async def patch_user(
    user_id: int = Path(..., ge=1),
    payload: UserUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Partially update the authenticated user's own profile.
    Allowed fields: name, email, password (plain text). Password will be hashed.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")

    patch = payload.model_dump(exclude_unset=True)
    try:
        updated = await user_service.update_user(db=db, user_id=user_id, patch=patch, requester_user_id=current_user.id)
    except ValueError as exc:
        # e.g., email already in use or user not found
        detail = str(exc)
        code = status.HTTP_400_BAD_REQUEST if "email" in detail.lower() or "already" in detail.lower() else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=detail)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error updating user id=%s: %s", user_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    return UserOut.model_validate(updated, from_attributes=True)


# --- Delete user (owner only) --------------------------------------------
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Delete the authenticated user's account (self-delete). Returns 204 on success.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user")

    try:
        await user_service.delete_user(db=db, user_id=user_id, requester_user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error deleting user id=%s: %s", user_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    return None
