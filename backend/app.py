"""
RoboCode RAG — Unified Application Entrypoint
Exposes the production FastAPI application from backend.main, ensuring complete
hybrid retrieval, robotics static audit, and grounded LLM answering.
"""

from backend.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
