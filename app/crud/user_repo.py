# app/repositories/user_repo.py
from typing import Optional
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

# module-level instance (easy import in services)
user_repo = UserRepository()