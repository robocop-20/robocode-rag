import pytest
import pathlib
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_index_and_query_pipeline():
    project_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "examples" / "diffbot_firmware"
    
    # 1. Index the sample robotics directory
    index_res = client.post("/api/index", json={"project_path": str(project_dir)})
    assert index_res.status_code == 200
    data = index_res.json()
    assert data["status"] == "success"
    assert data["files_indexed"] >= 2
    assert data["chunks_indexed"] >= 2

    # 2. Query for PID computation
    query_res = client.post("/api/query", json={"query": "compute_pid error feedback", "top_k": 3})
    assert query_res.status_code == 200
    q_data = query_res.json()
    assert len(q_data["citations"]) > 0
    assert "diffbot_controller.cpp" in q_data["citations"][0]["file_path"]
    assert "compute_pid" in q_data["citations"][0]["snippet"]
    assert len(q_data["answer"]) > 50

    # 3. Query for ROS topics
    topic_res = client.post("/api/query", json={"query": "cmd_vel subscriber velocity", "top_k": 3})
    assert topic_res.status_code == 200
    t_data = topic_res.json()
    assert any("/cmd_vel" in c["snippet"] for c in t_data["citations"])
