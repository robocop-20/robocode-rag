import os
import pathlib
import sqlite3
from typing import List, Tuple
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel

app = FastAPI()

DB_PATH = pathlib.Path(__file__).parent / "robocode.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Create files table
    c.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE,
        language TEXT,
        size INTEGER
    )
    """)
    # Create chunks table with FTS5 for content search
    c.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
        file_id UNINDEXED,
        chunk_id UNINDEXED,
        content,
        start_line UNINDEXED,
        end_line UNINDEXED,
        tokenize='porter'
    );
    """)
    conn.commit()
    conn.close()

init_db()

CHUNK_SIZE = 200  # lines per chunk

def chunk_file(content: str) -> List[Tuple[int, int, str]]:
    lines = content.splitlines()
    chunks = []
    for i in range(0, len(lines), CHUNK_SIZE):
        chunk_lines = lines[i:i+CHUNK_SIZE]
        start = i + 1
        end = i + len(chunk_lines)
        chunks.append((start, end, "\n".join(chunk_lines)))
    return chunks

def detect_language(file_path: str) -> str:
    ext = pathlib.Path(file_path).suffix.lower()
    if ext in {".py", ".pyi"}:
        return "python"
    if ext in {".cpp", ".cc", ".cxx", ".hpp", ".h", ".hh"}:
        return "cpp"
    if ext == ".c":
        return "c"
    if ext == ".rs":
        return "rust"
    if ext == ".js":
        return "javascript"
    if ext == ".ts":
        return "typescript"
    if ext == ".java":
        return "java"
    if ext == ".go":
        return "go"
    return "plaintext"

class IndexRequest(BaseModel):
    project_path: str  # absolute path to project directory
    exclude_dirs: List[str] = []
    exclude_patterns: List[str] = []  # glob patterns to ignore

@app.post("/index")
def index_project(req: IndexRequest):
    project_root = pathlib.Path(req.project_path)
    if not project_root.is_dir():
        raise HTTPException(status_code=400, detail="Project path must be a directory")

    conn = get_db_connection()
    cur = conn.cursor()

    for root, dirs, files in os.walk(project_root):
        # Apply directory exclusions
        dirs[:] = [d for d in dirs if d not in req.exclude_dirs]
        for file in files:
            file_path = pathlib.Path(root) / file
            rel_path = file_path.relative_to(project_root)
            # Simple exclusion based on patterns (could be expanded)
            if any(file_path.match(p) for p in req.exclude_patterns):
                continue
            # Skip binary files
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            language = detect_language(str(file_path))
            size = os.path.getsize(file_path)
            # Insert or ignore file record
            cur.execute(
                "INSERT OR IGNORE INTO files (path, language, size) VALUES (?, ?, ?)",
                (str(rel_path), language, size),
            )
            cur.execute("SELECT id FROM files WHERE path = ?", (str(rel_path),))
            file_id = cur.fetchone()[0]
            # Chunk and index
            for idx, (start, end, chunk_content) in enumerate(chunk_file(content), start=1):
                cur.execute(
                    "INSERT INTO chunks (file_id, chunk_id, content, start_line, end_line) VALUES (?, ?, ?, ?, ?)",
                    (file_id, idx, chunk_content, start, end),
                )
    conn.commit()
    conn.close()
    return {"status": "indexing complete"}

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class SourceCitation(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    snippet: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[SourceCitation]

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    # Simple lexical search using FTS5 bm25 ranking
    cur.execute(
        "SELECT file_id, chunk_id, content, start_line, end_line, bm25(chunks) AS rank "
        "FROM chunks WHERE chunks MATCH ? ORDER BY rank LIMIT ?",
        (req.query, req.top_k),
    )
    rows = cur.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="No relevant chunks found")
    # Retrieve file paths
    citations = []
    for file_id, chunk_id, content, start_line, end_line, _ in rows:
        cur.execute("SELECT path FROM files WHERE id = ?", (file_id,))
        file_path = cur.fetchone()[0]
        citations.append(
            SourceCitation(
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                snippet=content,
            )
        )
    # Placeholder answer – real implementation would call a local LLM
    answer = "(Answer generation not yet implemented – integrate a local LLM for grounded responses.)"
    conn.close()
    return QueryResponse(answer=answer, citations=citations)
