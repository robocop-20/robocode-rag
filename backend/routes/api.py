import os
import time
import pathlib
import zipfile
import shutil
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from backend.config import DEFAULT_TOP_K, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, DATA_DIR
from backend.database import get_db_connection, clear_database, get_db_stats
from backend.parsers.language import detect_language
from backend.parsers.chunker import chunk_file_content
from backend.parsers.robotics_analyzer import analyze_robotics_code
from backend.retrieval.hybrid_retriever import retriever
from backend.retrieval.vector_store import vector_store
from backend.generation.llm_client import llm_client

router = APIRouter(prefix="/api")

class IndexRequest(BaseModel):
    project_path: str
    exclude_dirs: List[str] = [".git", "node_modules", "build", "devel", "install", "__pycache__", ".venv"]
    exclude_patterns: List[str] = ["*.pyc", "*.so", "*.a", "*.o", "*.bin"]

class QueryRequest(BaseModel):
    query: str
    top_k: int = DEFAULT_TOP_K

class SourceCitation(BaseModel):
    file_path: str
    language: str
    start_line: int
    end_line: int
    symbol_name: Optional[str] = ""
    snippet: str
    relevance_score: float

class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[SourceCitation]
    latency_ms: float
    total_found: int

class CodeAnalysisRequest(BaseModel):
    code: str
    language: str = "cpp"
    file_name: str = "main.cpp"

@router.post("/index")
def index_directory(req: IndexRequest):
    project_root = pathlib.Path(req.project_path).resolve()
    if not project_root.exists() or not project_root.is_dir():
        raise HTTPException(status_code=400, detail=f"Invalid directory path: {req.project_path}")

    conn = get_db_connection()
    cur = conn.cursor()

    indexed_files = 0
    indexed_chunks = 0
    all_chunks_for_vectors = []

    for root, dirs, files in os.walk(project_root):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in req.exclude_dirs and not d.startswith(".")]

        for filename in files:
            file_path = pathlib.Path(root) / filename
            rel_path = str(file_path.relative_to(project_root)).replace("\\", "/")

            if any(file_path.match(p) for p in req.exclude_patterns):
                continue

            lang = detect_language(str(file_path))
            # Only index known source code, config, or robotics formats
            if lang in ["plaintext", "text"] and file_path.suffix not in [".txt", ".md", ""]:
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            if not content.strip():
                continue

            size = len(content.encode("utf-8"))

            # Remove existing records if this file was previously indexed
            cur.execute("SELECT id FROM files WHERE path = ?;", (str(file_path),))
            existing = cur.fetchone()
            if existing:
                old_id = existing[0]
                cur.execute("DELETE FROM chunks WHERE file_id = ?;", (old_id,))
                cur.execute("DELETE FROM robotics_nodes WHERE file_id = ?;", (old_id,))
                cur.execute("DELETE FROM files WHERE id = ?;", (old_id,))

            # Save file record
            cur.execute(
                "INSERT INTO files (path, rel_path, language, size) VALUES (?, ?, ?, ?);",
                (str(file_path), rel_path, lang, size),
            )
            file_id = cur.lastrowid

            # Analyze robotics features
            analysis = analyze_robotics_code(content, lang, str(file_path))
            cur.execute(
                """
                INSERT INTO robotics_nodes (file_id, node_name, framework, publishers, subscribers, services, realtime_issues)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    file_id,
                    rel_path,
                    analysis["framework"],
                    str(analysis["publishers"]),
                    str(analysis["subscribers"]),
                    str(analysis["services"]),
                    str(analysis["realtime_issues"]),
                ),
            )

            # Chunk file
            chunks = chunk_file_content(content, chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP)
            for c in chunks:
                flags = ",".join(analysis["flags"])
                cur.execute(
                    """
                    INSERT INTO chunks (content, file_id, chunk_id, start_line, end_line, symbol_name, robotics_flags)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (c["content"], file_id, c["chunk_id"], c["start_line"], c["end_line"], c["symbol_name"], flags),
                )
                all_chunks_for_vectors.append({
                    "file_id": file_id,
                    "file_path": rel_path,
                    "language": lang,
                    "chunk_id": c["chunk_id"],
                    "content": c["content"],
                    "symbol_name": c["symbol_name"],
                    "start_line": c["start_line"],
                    "end_line": c["end_line"],
                })
                indexed_chunks += 1

            indexed_files += 1

    conn.commit()
    conn.close()

    # Index into vector store
    vector_store.add_documents(all_chunks_for_vectors)

    return {
        "status": "success",
        "message": f"Successfully indexed {indexed_files} files into {indexed_chunks} chunks.",
        "files_indexed": indexed_files,
        "chunks_indexed": indexed_chunks,
    }

@router.post("/upload")
async def upload_files_or_zip(file: UploadFile = File(...)):
    """
    Allow uploading a zip file or single code file directly via browser on Render.
    """
    upload_dir = DATA_DIR / "uploads" / str(int(time.time()))
    upload_dir.mkdir(parents=True, exist_ok=True)

    dest_path = upload_dir / file.filename
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    extract_path = upload_dir / "extracted"
    if zipfile.is_zipfile(dest_path):
        with zipfile.ZipFile(dest_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
        target_index_path = str(extract_path)
    else:
        target_index_path = str(upload_dir)

    # Trigger indexing on the uploaded files
    index_req = IndexRequest(project_path=target_index_path)
    res = index_directory(index_req)
    return {
        "upload_status": "success",
        "filename": file.filename,
        "index_result": res,
    }

@router.post("/query", response_model=QueryResponse)
async def query_codebase(req: QueryRequest):
    start_time = time.perf_counter()
    citations_data = retriever.retrieve(req.query, top_k=req.top_k)

    if not citations_data:
        raise HTTPException(
            status_code=404,
            detail="No relevant code chunks found. Ensure you have indexed files via the Indexer tab first."
        )

    citations = [SourceCitation(**c) for c in citations_data]
    answer = await llm_client.generate_answer(req.query, citations_data)
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return QueryResponse(
        query=req.query,
        answer=answer,
        citations=citations,
        latency_ms=latency_ms,
        total_found=len(citations),
    )

@router.get("/status")
def get_system_status():
    stats = get_db_stats()
    return {
        "status": "online",
        "stats": stats,
    }

@router.post("/analyze-robotics")
def analyze_code_snippet(req: CodeAnalysisRequest):
    analysis = analyze_robotics_code(req.code, req.language, req.file_name)
    return {
        "file_name": req.file_name,
        "language": req.language,
        "analysis": analysis,
    }

@router.post("/clear")
def clear_all_indexes():
    clear_database()
    vector_store.clear()
    return {"status": "cleared", "message": "Indexed files and chunks removed."}
