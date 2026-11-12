import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.crud.user_repo import user_repo
from app.models.project import Project
from app.services.project_service import project_service
from app.services.task_service import task_service
from app.services.user_service import user_service

DEMO_EMAIL = "demo@taskmanager.local"
DEMO_PASSWORD = "demo1234"
ADMIN_EMAIL = "admin@taskmanager.local"
ADMIN_PASSWORD = "admin1234"
LEAD_EMAIL = "lead@taskmanager.local"
LEAD_PASSWORD = "lead1234"
MEMBER_EMAIL = "member@taskmanager.local"
MEMBER_PASSWORD = "member1234"
SAMPLE_PROJECT = "Product launch"


async def _ensure_user(db, email: str, password: str, name: str, role: str):
    """Create the user or keep role/password in sync for seed accounts."""
    existing = await user_repo.get_by_email(db, email)
    if existing:
        existing.role = role
        existing.name = name
        existing.password_hash = user_service.hash_password(password)
        await db.commit()
        await db.refresh(existing)
        return existing
    user = await user_service.create_user(
        db,
        email=email,
        password=password,
        name=name,
        phone=None,
        role=role,
    )
    print(f"Seeded {role} {email}")
    return user


async def run_seed(db) -> None:
    """Create one account per role, plus a sample project a lead and member can open."""
    await _ensure_user(db, ADMIN_EMAIL, ADMIN_PASSWORD, "Avery Admin", "admin")
    # Second built-in admin for demos / backup access
    await _ensure_user(db, "owner@taskmanager.local", "owner1234", "Owner Admin", "admin")
    lead = await _ensure_user(db, LEAD_EMAIL, LEAD_PASSWORD, "Jordan Lead", "project_lead")
    member = await _ensure_user(db, MEMBER_EMAIL, MEMBER_PASSWORD, "Sam Member", "member")
    await _ensure_user(db, DEMO_EMAIL, DEMO_PASSWORD, "Demo User", "member")

    # Optional extra admin from env (useful on Render / demos)
    extra_email = (os.getenv("SEED_ADMIN_EMAIL") or "").strip().lower()
    extra_password = (os.getenv("SEED_ADMIN_PASSWORD") or "").strip()
    extra_name = (os.getenv("SEED_ADMIN_NAME") or "Workspace Admin").strip()
    if extra_email and extra_password and extra_email not in {ADMIN_EMAIL, "owner@taskmanager.local"}:
        await _ensure_user(db, extra_email, extra_password, extra_name, "admin")
        print(f"Seeded extra admin {extra_email}")

    existing = (
        await db.execute(select(Project).where(Project.name == SAMPLE_PROJECT))
    ).scalar_one_or_none()
    if existing:
        return

    admin = await user_repo.get_by_email(db, ADMIN_EMAIL)
    project = await project_service.create_project(
        db,
        name=SAMPLE_PROJECT,
        description="Sample workspace so each role has something to open.",
    )
    await project_service.set_members(db, project.id, [lead.id, member.id])
    due = datetime.now(timezone.utc) + timedelta(days=5)
    await task_service.create_task(
        db,
        creator_id=admin.id,
        title="Draft the launch checklist",
        description="Collect the tasks the team still owes before launch day.",
        project_id=project.id,
        assignee_ids=[member.id],
        priority=2,
        due_at=due,
        status="todo",
    )
    await task_service.create_task(
        db,
        creator_id=admin.id,
        title="Review the homepage copy",
        description="Read the draft and note what still feels unclear.",
        project_id=project.id,
        assignee_ids=[member.id],
        priority=3,
        status="in_progress",
    )
    print(f"Seeded sample project {SAMPLE_PROJECT}")
