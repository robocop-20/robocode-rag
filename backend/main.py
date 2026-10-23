import os
import pathlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import CORS_ORIGINS
from backend.database import init_db
from backend.routes.health import router as health_router
from backend.routes.api import router as api_router

# Initialize database schema upon startup
init_db()

app = FastAPI(
    title="RoboCode RAG",
    description="Autonomous AI Coding Assistant & RAG Engine for Robotics and Embedded Systems",
    version="1.0.0",
)

# Enable CORS for web apps & IDE extensions
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(api_router)

# Mount frontend static files
STATIC_DIR = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "service": "RoboCode RAG",
        "status": "online",
        "docs_url": "/docs",
        "health_check": "/health",
    }
