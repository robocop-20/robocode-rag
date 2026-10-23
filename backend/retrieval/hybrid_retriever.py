import re
import sqlite3
from typing import List, Dict, Any
from backend.database import get_db_connection
from backend.retrieval.vector_store import vector_store

def sanitize_fts_query(query: str) -> str:
    # Remove FTS5 operators and punctuation that can cause syntax errors
    tokens = re.findall(r"[A-Za-z0-9_]+", query)
    if not tokens:
        return '""'
    # Use OR or NEAR search for broader recall
    return " OR ".join(tokens)

class HybridRetriever:
    @staticmethod
    def retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()

        fts_query = sanitize_fts_query(query)
        bm25_results = []
        try:
            cur.execute(
                """
                SELECT file_id, chunk_id, content, start_line, end_line, symbol_name, bm25(chunks) AS rank
                FROM chunks
                WHERE chunks MATCH ?
                ORDER BY rank
                LIMIT ?;
                """,
                (fts_query, top_k * 3),
            )
            rows = cur.fetchall()
            for r in rows:
                bm25_results.append({
                    "file_id": r[0],
                    "chunk_id": r[1],
                    "content": r[2],
                    "start_line": r[3],
                    "end_line": r[4],
                    "symbol_name": r[5] or "",
                    "bm25_score": abs(float(r[6])),
                })
        except sqlite3.OperationalError:
            bm25_results = []

        # 2. Vector Store (Semantic) Search
        vector_results = vector_store.search(query, top_k=top_k * 3)

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF score = 1 / (60 + rank)
        fused_scores: Dict[str, Dict[str, Any]] = {}

        for rank, item in enumerate(bm25_results):
            key = f"{item['file_id']}_{item['chunk_id']}"
            if key not in fused_scores:
                fused_scores[key] = {
                    "item": item,
                    "rrf_score": 0.0,
                    "bm25_rank": rank,
                    "vector_rank": None,
                }
            fused_scores[key]["rrf_score"] += 1.0 / (60.0 + rank)

        for rank, (doc, sim) in enumerate(vector_results):
            key = f"{doc['file_id']}_{doc['chunk_id']}"
            if key not in fused_scores:
                fused_scores[key] = {
                    "item": doc,
                    "rrf_score": 0.0,
                    "bm25_rank": None,
                    "vector_rank": rank,
                }
            fused_scores[key]["rrf_score"] += 1.0 / (60.0 + rank)

        sorted_items = sorted(fused_scores.values(), key=lambda x: x["rrf_score"], reverse=True)

        # 4. Resolve file paths and build final citations
        final_citations = []
        for entry in sorted_items[:top_k]:
            item = entry["item"]
            file_id = item["file_id"]
            cur.execute("SELECT path, rel_path, language FROM files WHERE id = ?;", (file_id,))
            file_row = cur.fetchone()
            file_path = file_row[1] if file_row and file_row[1] else (file_row[0] if file_row else item.get("file_path"))
            if not file_path:
                continue
            language = file_row[2] if file_row else item.get("language", "text")

            final_citations.append({
                "file_path": file_path,
                "language": language,
                "start_line": item["start_line"],
                "end_line": item["end_line"],
                "symbol_name": item.get("symbol_name", ""),
                "snippet": item["content"],
                "relevance_score": round(entry["rrf_score"] * 100, 2),
            })

        conn.close()
        return final_citations

retriever = HybridRetriever()
