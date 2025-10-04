# app/api/v1/routers/users_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

# app/api/v1/routers/users_router.py (fixed)
from app.schemas.user_schema import UserCreate, UserOut, TokenOut


from app.services.user_service import user_service
from app.api.v1.dependencies import get_db  # your DB dependency

router = APIRouter()  # <--- NO prefix here

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db=Depends(get_db)):
    user = await user_service.create_user(db=db, email=payload.email, password=payload.password, name=payload.name)
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
