import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repo import user_repo
from app.models.user import User
from app.schemas.user_schema import UserCreate

# Load secrets from .env
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "replace-this-with-strong-secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Service layer for user operations."""

    async def register_user(self, db: AsyncSession, payload: UserCreate) -> User:
        """Create a new user with hashed password."""
        existing = await user_repo.get_by_email(db, payload.email)
        if existing:
            raise ValueError("User with this email already exists")

        hashed_password = self.hash_password(payload.password)
        user = await user_repo.create(
            db,
            email=payload.email,
            password_hash=hashed_password,
            name=payload.name
        )
        return user
    
    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        user = await user_repo.get_by_email(db, email)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    def hash_password(self, password: str) -> str:
        """Hash plain password."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against the hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    
    def create_access_token(self, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = {"sub": str(user_id)}
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def decode_access_token(self, token: str) -> Optional[int]:
        """Decode JWT and return user_id."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = int(payload.get("sub"))
            return user_id
        except (JWTError, TypeError, ValueError):
            return None
        
        
# module-level instance
user_service = UserService()