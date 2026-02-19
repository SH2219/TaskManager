# app/services/projectmembers_service.py
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.projectmembers_repo import projectmembers_repo
from app.crud.user_repo import user_repo
from app.crud.project_repo import project_repo
from app.models.projectmembers import ProjectMembers

# allowed per-project roles
PROJECT_ROLES = {"member", "manager", "owner"}

class ProjectMembersService:
    async def _ensure_project_exists(self, db: AsyncSession, project_id: int):
        project = await project_repo.get(db, project_id)
        if not project:
            raise ValueError("Project not found")
        return project
    
    async def _ensure_user_exists(self, db: AsyncSession, user_id: int):
        user = await user_repo.get(db, user_id)
        if not user:
            raise ValueError("User not found")
        return user
    
    async def create_membership(self, db: AsyncSession, requester_user, *, project_id: int, user_id: int, role: str) -> ProjectMembers:
        if role not in PROJECT_ROLES:
            raise ValueError(f"Invalid role: {role}")

        await self._ensure_project_exists(db, project_id)
        await self._ensure_user_exists(db, user_id)
        
        # permission: global admin OR project owner/manager can add
        if getattr(requester_user, "role", None) != "admin":
            pm_req = await projectmembers_repo.get_by_project_user(db, project_id, requester_user.id)
            if not pm_req or pm_req.role not in ("owner", "manager"):
                raise PermissionError("Not authorized to add members to this project")
            
        existing = await projectmembers_repo.get_by_project_user(db, project_id, user_id)
        if existing:
            raise ValueError("User is already a member of the project")

        pm = await projectmembers_repo.create(db, project_id=project_id, user_id=user_id, role=role, added_by=requester_user.id)
        await db.commit()
        await db.refresh(pm)
        return pm
    
    async def list_members(self, db: AsyncSession, project_id: int, skip: int = 0, limit: int = 100) -> List[ProjectMembers]:
        await self._ensure_project_exists(db, project_id)
        return await projectmembers_repo.list_by_project(db, project_id, skip=skip, limit=limit)


    async def get_membership(self, db: AsyncSession, membership_id: int) -> Optional[ProjectMembers]:
        return await projectmembers_repo.get(db, membership_id)

    async def update_membership(self, db: AsyncSession, requester_user, membership_id: int, patch: Dict) -> Optional[ProjectMembers]:
        pm = await projectmembers_repo.get(db, membership_id)
        if not pm:
            return None
        
        
        # permission: only global admin or project owner can change roles
        if getattr(requester_user, "role", None) != "admin":
            pm_req = await projectmembers_repo.get_by_project_user(db, pm.project_id, requester_user.id)
            if not pm_req or pm_req.role != "owner":
                raise PermissionError("Not authorized to update membership")

        new_role = patch.get("role")
        if new_role and new_role not in PROJECT_ROLES:
            raise ValueError("Invalid role")

        pm = await projectmembers_repo.update(db, pm, patch)
        await db.commit()
        await db.refresh(pm)
        return pm
    
    
    async def delete_membership(self, db: AsyncSession, requester_user, membership_id: int) -> None:
        pm = await projectmembers_repo.get(db, membership_id)
        if not pm:
            raise ValueError("Membership not found")

        # permission: global admin or owner can remove; allow self-remove
        if getattr(requester_user, "role", None) == "admin":
            pass
        elif pm.user_id == requester_user.id:
            pass
        else:
            pm_req = await projectmembers_repo.get_by_project_user(db, pm.project_id, requester_user.id)
            if not pm_req or pm_req.role != "owner":
                raise PermissionError("Not authorized to remove membership")

        await projectmembers_repo.delete(db, pm)
        await db.commit()


projectmembers_service = ProjectMembersService()
