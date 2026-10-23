import sqlite3
import pathlib
from typing import Dict, Any, List
from backend.config import DB_PATH

def get_db_connection() -> sqlite3.Connection:
    pathlib.Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Track indexed files
    c.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE,
        rel_path TEXT,
        language TEXT,
        size INTEGER,
        indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Track robotics-specific nodes, topics, hardware pins
    c.execute("""
    CREATE TABLE IF NOT EXISTS robotics_nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER,
        node_name TEXT,
        framework TEXT, -- ros1, ros2, arduino, rtos, micro_ros
        publishers TEXT, -- JSON array
        subscribers TEXT, -- JSON array
        services TEXT, -- JSON array
        realtime_issues TEXT, -- JSON array of detected real-time violations
        FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
    );
    """)

    # Create FTS5 virtual table for lexical BM25 search
    # Notice: All columns except content marked UNINDEXED to optimize index performance
    c.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
        content,
        file_id UNINDEXED,
        chunk_id UNINDEXED,
        start_line UNINDEXED,
        end_line UNINDEXED,
        symbol_name UNINDEXED,
        robotics_flags UNINDEXED,
        tokenize='porter unicode61'
    );
    """)

    conn.commit()
    conn.close()

def clear_database():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM chunks;")
    cur.execute("DELETE FROM robotics_nodes;")
    cur.execute("DELETE FROM files;")
    conn.commit()
    conn.close()

def get_db_stats() -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM files;")
        file_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM chunks;")
        chunk_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM robotics_nodes;")
        node_count = cur.fetchone()[0]
        cur.execute("SELECT language, COUNT(*) FROM files GROUP BY language;")
        lang_counts = dict(cur.fetchall())
        return {
            "total_files": file_count,
            "total_chunks": chunk_count,
            "total_robotics_nodes": node_count,
            "languages": lang_counts,
        }
    finally:
        conn.close()
