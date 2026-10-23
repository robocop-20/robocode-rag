import pytest
from backend.parsers.robotics_analyzer import analyze_robotics_code

def test_ros2_pub_sub_detection():
    cpp_code = """
    class DriveNode : public rclcpp::Node {
    public:
        DriveNode() : Node("drive_node") {
            pub_ = this->create_publisher<geometry_msgs::msg::Twist>("cmd_vel", 10);
            sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>("scan", 10, callback);
        }
    };
    """
    res = analyze_robotics_code(cpp_code, "cpp")
    assert res["framework"] == "ros2"
    assert len(res["publishers"]) == 1
    assert res["publishers"][0]["topic"] == "cmd_vel"
    assert len(res["subscribers"]) == 1
    assert res["subscribers"][0]["topic"] == "scan"

def test_realtime_violation_detection():
    cpp_code = """
    void control_loop() {
        delay(10);
        int* arr = new int[50];
        delete[] arr;
    }
    """
    res = analyze_robotics_code(cpp_code, "cpp")
    issues = res["realtime_issues"]
    assert len(issues) >= 1
    types = [i["type"] for i in issues]
    assert "blocking_delay" in types
