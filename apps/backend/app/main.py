# app/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

# load environment variables from .env
load_dotenv()

# import DB Base and async engine (these names must match your database module)
from app.core.database import Base, engine
from app.models import TaskAssignment, ProjectMember, Notification  # register models for create_all

# import routers (these should export an APIRouter object called `router`)
from app.api.users_router import router as users_router
from app.api.projects_router import router as projects_router
from app.api.tasks_router import router as tasks_router
from app.api.tags_router import router as tags_router
from app.api.comments_router import router as comments_router
from app.api.ai_router import router as ai_router
from app.api.notifications_router import router as notifications_router


async def _migrate_schema(conn):
    """Add columns/tables when DB was created before newer features."""
    await conn.execute(text(
        "ALTER TABLE task_assignees ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0"
    ))
    await conn.execute(text(
        "ALTER TABLE task_assignees ADD COLUMN IF NOT EXISTS rating INTEGER"
    ))
    await conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT"
    ))
    await conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'member'"
    ))
    await conn.execute(text(
        "UPDATE users SET role = 'member' WHERE role IS NULL"
    ))
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS project_members (
            project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role TEXT DEFAULT 'member',
            PRIMARY KEY (project_id, user_id)
        )
    """))
    await conn.execute(text(
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ"
    ))
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS notifications (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            task_id BIGINT REFERENCES tasks(id) ON DELETE CASCADE,
            project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
            read_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id)"
    ))


# Lifespan handler — runs once on startup, once on shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_schema(conn)
    print("Database tables created successfully!")
    from app.core.database import async_session
    from app.core.seed import run_seed

    async with async_session() as db:
        await run_seed(db)
    try:
        yield
    finally:
        # any shutdown cleanup would go here
        pass

# Create FastAPI app with the lifespan handler
app = FastAPI(title="Task Manager API", lifespan=lifespan)

# Configure CORS (adjust origins for security; "*" is permissive)
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------- ROUTERS / API --------------
# IMPORTANT: Be careful with prefixes — see note below.
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(tags_router, prefix="/api", tags=["Tags"])
app.include_router(comments_router, prefix="/api", tags=["Comments"])
app.include_router(ai_router, prefix="/api/ai", tags=["AI"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])

# optional root route
@app.get("/", include_in_schema=False)
async def root():
    return {"status": "ok"}
