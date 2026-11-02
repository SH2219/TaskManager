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
    
    async def create(
        self,
        db: AsyncSession,
        *,
        email: str,
        password_hash: str,
        name: str | None = None,
        phone: str | None = None,
        role: str | None = "member",
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            phone=phone,
            role=role or "member",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    
    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
        result = await db.execute(select(User).order_by(User.id).offset(skip).limit(limit))
        return result.scalars().all()

    async def count_by_role(self, db: AsyncSession, role: str) -> int:
        from sqlalchemy import func

        result = await db.execute(select(func.count()).select_from(User).where(User.role == role))
        return int(result.scalar_one())

    async def update(self, db: AsyncSession, user: User, patch: dict) -> User:
        for key, value in patch.items():
            setattr(user, key, value)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def delete(self, db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.flush()

# module-level instance (easy import in services)
user_repo = UserRepository()
