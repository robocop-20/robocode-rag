import pytest
from backend.retrieval.vector_store import FastVectorStore, tokenize

def test_tokenize():
    tokens = tokenize("void imuCallback_Handler()")
    assert "imu" in tokens
    assert "callback" in tokens
    assert "handler" in tokens

def test_fast_vector_store():
    store = FastVectorStore()
    docs = [
        {"file_id": 1, "chunk_id": 1, "content": "PID motor speed controller with proportional gain kp"},
        {"file_id": 1, "chunk_id": 2, "content": "LiDAR pointcloud laser scan filtering node"},
        {"file_id": 2, "chunk_id": 1, "content": "CAN bus motor driver telemetry packet parser"},
    ]
    store.add_documents(docs)
    results = store.search("PID controller gain", top_k=2)
    assert len(results) > 0
    assert results[0][0]["chunk_id"] == 1
