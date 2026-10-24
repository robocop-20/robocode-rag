import os
import time
import logging
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import CORS_ORIGINS
from backend.database import init_db
from backend.routes.health import router as health_router
from backend.routes.api import router as api_router

# ─── Structured Logging ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("robocode")


# ─── Application Lifespan (startup / shutdown) ────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run once at startup, yield through the app's lifetime, cleanup on shutdown."""
    logger.info("Initializing database schema …")
    init_db()
    logger.info("RoboCode RAG is ready to serve requests.")
    yield
    logger.info("RoboCode RAG shutting down …")


app = FastAPI(
    title="RoboCode RAG",
    description="Autonomous AI Coding Assistant & RAG Engine for Robotics and Embedded Systems",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request Logging & Timing Middleware ───────────────────────────
@app.middleware("http")
async def log_and_time_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "%s %s → %s  (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
    return response


# ─── Include Routers ───────────────────────────────────────────────
app.include_router(health_router)
app.include_router(api_router)

# Backward-compatibility route aliases for root /query and /index
from backend.routes.api import query_codebase, index_directory, IndexRequest, QueryRequest

@app.post("/query", include_in_schema=False)
async def query_alias(req: QueryRequest):
    return await query_codebase(req)

@app.post("/index", include_in_schema=False)
def index_alias(req: IndexRequest):
    return index_directory(req)

# ─── Mount Frontend ───────────────────────────────────────────────
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
