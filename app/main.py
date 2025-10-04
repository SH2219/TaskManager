from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import routers
from app.api.v1.routers.users_router import router as users_router
from app.api.v1.routers.projects_router import router as projects_router
from app.api.v1.routers.tasks_router import router as tasks_router

# Import DB Base and engine
from app.database import Base, engine

app = FastAPI(title="Task Manager API")

# Allow CORS for frontend
origins = ["*"]  # You can restrict this to your frontend domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["Tasks"])

# Create tables on startup
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")
