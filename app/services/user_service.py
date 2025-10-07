# app/services/user_service.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user_repo import user_repo
from app.models.user import User
from app.schemas.user_schema import UserCreate

# Load secrets from environment
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "replace-this-with-strong-secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
# env vars are strings; ensure we convert safely
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Service layer for user operations."""

    # keep an async create_user for routers to await
    async def create_user(self, db: AsyncSession, email: str, password: str, name: Optional[str] = None) -> User:
        """
        Create a new user and persist to DB. Raises ValueError if email exists.
        This is async so router can: await user_service.create_user(...)
        """
        existing = await user_repo.get_by_email(db, email)
        if existing:
            raise ValueError("User with this email already exists")

        hashed_password = self.hash_password(password)
        user = await user_repo.create(db, email=email, password_hash=hashed_password, name=name)\
            # Commit here
        await db.commit()
        await db.refresh(user)
        return user

    # adapter to keep your previous register_user signature (if other code uses it)
    async def register_user(self, db: AsyncSession, payload: UserCreate) -> User:
        return await self.create_user(db, email=payload.email, password=payload.password, name=payload.name)

    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials (async)."""
        user = await user_repo.get_by_email(db, email)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    def hash_password(self, password: str) -> str:
        """Hash plain password (sync)."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against the hash (sync)."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT token (synchronous). Return string.
        Do NOT await this function in routes.
        """
        expire_time = datetime.now(timezone.utc) + (expires_delta if expires_delta is not None else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        # Use integer unix timestamp for exp to avoid compatibility issues:
        to_encode = {"sub": str(user_id), "exp": int(expire_time.timestamp())}
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def decode_access_token(self, token: str) -> Optional[int]:
        """Decode JWT and return user_id or None on failure."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            sub = payload.get("sub")
            if sub is None:
                return None
            return int(sub)
        except (JWTError, TypeError, ValueError):
            return None


# module-level instance
user_service = UserService()
