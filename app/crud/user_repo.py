# app/repositories/user_repo.py
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

class UserRepository:
    """Repository for User queries."""

    async def get(self, db: AsyncSession, user_id: int) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()
    
    async def create(self, db: AsyncSession, *, email: str, password_hash: str, name: str | None = None) -> User:
        user = User(email=email, password_hash=password_hash, name=name)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    
    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()
    
    
    
    async def update(self, db: AsyncSession, user: User, patch: Dict[str, Any]) -> User:
        """
        Apply patch dict to the given User ORM instance and return the instance.
        Note: commit/refresh handled by caller (service/router).
        """
        # Only allow certain fields to be written
        allowed = {"name", "email", "password_hash"}
        for k, v in patch.items():
            if k not in allowed:
                continue
            setattr(user, k, v)
        await db.flush()
        await db.refresh(user)
        return user

    async def delete(self, db: AsyncSession, user: User) -> None:
        """
        Permanently delete user. Caller should commit.
        """
        await db.delete(user)
        await db.flush()

# module-level instance (easy import in services)
user_repo = UserRepository()