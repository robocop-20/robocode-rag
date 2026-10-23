import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "robocode-rag"

def test_status_endpoint():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "stats" in data

def test_robotics_analysis_endpoint():
    sample_code = """
    class ArmController : public rclcpp::Node {
    public:
        ArmController() : Node("arm_controller") {
            joint_pub = this->create_publisher<sensor_msgs::msg::JointState>("joint_states", 10);
        }
    };
    """
    res = client.post("/api/analyze-robotics", json={
        "code": sample_code,
        "language": "cpp",
        "file_name": "arm.cpp"
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["analysis"]["publishers"]) == 1
