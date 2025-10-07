# app/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# load environment variables from .env
load_dotenv()

# import DB Base and async engine (these names must match your database module)
from core.database import Base, engine

# import routers (these should export an APIRouter object called `router`)
from app.api.users_router import router as users_router
from app.api.projects_router import router as projects_router
from app.api.tasks_router import router as tasks_router

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

# optional root route
@app.get("/", include_in_schema=False)
async def root():
    return {"status": "ok"}
