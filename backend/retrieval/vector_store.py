import math
import re
from typing import List, Dict, Any, Tuple
from collections import Counter

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]{2,}")

def tokenize(text: str) -> List[str]:
    # Extract code and text tokens, with snake_case and camelCase decomposition
    raw_tokens = TOKEN_PATTERN.findall(text)
    sub_tokens = []
    for raw in raw_tokens:
        sub_tokens.append(raw.lower())
        # Split on underscores
        parts = [p for p in raw.split("_") if p]
        for part in parts:
            sub_tokens.append(part.lower())
            # Split camelCase: e.g. "imuCallback" -> "imu", "Callback"
            camel_parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", part)
            if len(camel_parts) > 1:
                sub_tokens.extend([cp.lower() for cp in camel_parts if len(cp) > 1])
    return [t for t in sub_tokens if len(t) > 1]

class FastVectorStore:
    """
    Lightweight, high-speed in-memory subword TF-IDF vector index.
    Zero external heavy dependencies like torch/transformers required,
    making it ideal for instant cold starts on Render's free tier.
    """
    def __init__(self):
        self.doc_vectors: List[Dict[str, float]] = []
        self.doc_metadata: List[Dict[str, Any]] = []
        self.doc_freq: Counter = Counter()
        self.total_docs: int = 0

    def clear(self):
        self.doc_vectors.clear()
        self.doc_metadata.clear()
        self.doc_freq.clear()
        self.total_docs = 0

    def add_documents(self, documents: List[Dict[str, Any]]):
        for doc in documents:
            tokens = tokenize(doc.get("content", ""))
            tf = Counter(tokens)
            self.total_docs += 1
            for term in set(tokens):
                self.doc_freq[term] += 1
            self.doc_vectors.append(tf)
            self.doc_metadata.append(doc)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        if self.total_docs == 0:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        q_tf = Counter(query_tokens)
        q_weights = {}
        for term, count in q_tf.items():
            idf = math.log((self.total_docs + 1) / (self.doc_freq.get(term, 0) + 1)) + 1.0
            q_weights[term] = count * idf

        q_norm = math.sqrt(sum(w * w for w in q_weights.values()))
        if q_norm == 0:
            return []

        scores: List[Tuple[int, float]] = []
        for idx, doc_tf in enumerate(self.doc_vectors):
            dot = 0.0
            doc_norm_sq = 0.0
            for term, count in doc_tf.items():
                idf = math.log((self.total_docs + 1) / (self.doc_freq.get(term, 0) + 1)) + 1.0
                weight = count * idf
                doc_norm_sq += weight * weight
                if term in q_weights:
                    dot += q_weights[term] * weight

            if dot > 0 and doc_norm_sq > 0:
                similarity = dot / (q_norm * math.sqrt(doc_norm_sq))
                scores.append((idx, similarity))

        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, sim in scores[:top_k]:
            results.append((self.doc_metadata[idx], sim))
        return results

vector_store = FastVectorStore()
