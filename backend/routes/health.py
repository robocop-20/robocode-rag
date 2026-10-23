from fastapi import APIRouter
from backend.database import get_db_stats

router = APIRouter()

@router.get("/health")
def health_check():
    stats = get_db_stats()
    return {
        "status": "healthy",
        "service": "robocode-rag",
        "version": "1.0.0",
        "database": {
            "status": "connected",
            "files_indexed": stats["total_files"],
            "chunks_indexed": stats["total_chunks"],
        }
    }
