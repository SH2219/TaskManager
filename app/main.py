# app/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# load environment variables from .env
load_dotenv()

# import DB Base and async engine (these names must match your database module)
from app.core.database import Base, engine

# import routers (these should export an APIRouter object called `router`)
from app.api.users_router import router as users_router
from app.api.projects_router import router as projects_router
from app.api.tasks_router import router as tasks_router
from app.api.tags_router import router as tags_router
from app.api.comments_router import router as comments_router
from app.api.progress_router import router as progress_router
# from app.api.projectmembers_router import router as projectmembers_router
# Lifespan handler — runs once on startup, once on shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all tables exist before the app starts accepting requests.
    # Using the async engine we open a connection and run the synchronous
    # metadata.create_all in a thread-safe way via run_sync.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")
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

app.include_router(progress_router, prefix="/api", tags=["Progress"])
# app.include_router(projectmembers_router, prefix="/api", tags=["ProjectMembers"])

# optional root route
@app.get("/", include_in_schema=False)
async def root():
    return {"status": "ok"}
