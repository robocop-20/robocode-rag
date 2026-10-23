import re
from typing import Dict, List, Any

# Pattern definitions for ROS 1 and ROS 2
ROS2_PUBLISHER = re.compile(r'create_publisher\s*<\s*([^>]+)\s*>\s*\(\s*["\']([^"\']+)["\']')
ROS2_SUBSCRIBER = re.compile(r'create_subscription\s*<\s*([^>]+)\s*>\s*\(\s*["\']([^"\']+)["\']')
ROS2_SERVICE = re.compile(r'create_service\s*<\s*([^>]+)\s*>\s*\(\s*["\']([^"\']+)["\']')
ROS2_NODE_INIT = re.compile(r'class\s+([A-Za-z0-9_]+)\s*:\s*public\s+rclcpp::Node|rclcpp::Node\s*\(\s*["\']([^"\']+)["\']')

ROS1_PUBLISHER = re.compile(r'advertise\s*<\s*([^>]+)\s*>\s*\(\s*["\']([^"\']+)["\']')
ROS1_SUBSCRIBER = re.compile(r'subscribe\s*<\s*([^>]+)\s*>\s*\(\s*["\']([^"\']+)["\']|subscribe\s*\(\s*["\']([^"\']+)["\']')
ROS1_NODE_INIT = re.compile(r'ros::init\s*\([^,]+,[^,]+,\s*["\']([^"\']+)["\']')

# Python ROS (rospy / rclpy)
PY_ROS2_PUB = re.compile(r'create_publisher\s*\(\s*([A-Za-z0-9_.]+)\s*,\s*["\']([^"\']+)["\']')
PY_ROS2_SUB = re.compile(r'create_subscription\s*\(\s*([A-Za-z0-9_.]+)\s*,\s*["\']([^"\']+)["\']')
PY_ROS1_PUB = re.compile(r'rospy\.Publisher\s*\(\s*["\']([^"\']+)["\']\s*,\s*([A-Za-z0-9_.]+)')
PY_ROS1_SUB = re.compile(r'rospy\.Subscriber\s*\(\s*["\']([^"\']+)["\']\s*,\s*([A-Za-z0-9_.]+)')

# Real-Time & Embedded Safety Violation Patterns
BLOCKING_CALLS = [
    (re.compile(r'\bdelay\s*\(\s*\d+\s*\)'), "Arduino delay() blocks execution loop; use non-blocking millis() timer"),
    (re.compile(r'\bsleep\s*\('), "POSIX sleep() introduces non-deterministic latency in real-time loop"),
    (re.compile(r'std::this_thread::sleep_for'), "sleep_for blocks OS thread; not deterministic for RT controller"),
    (re.compile(r'rclcpp::sleep_for'), "rclcpp::sleep_for inside callback delays executor thread queue"),
    (re.compile(r'ros::Duration\([^)]+\)\.sleep\(\)'), "ros::Duration sleep blocks ROS spinner loop"),
]

DYNAMIC_ALLOC_PATTERNS = [
    (re.compile(r'\bmalloc\s*\('), "malloc() inside real-time context causes non-deterministic heap fragmentation"),
    (re.compile(r'\bfree\s*\('), "free() inside control loop can trigger variable latency heap coalescing"),
    (re.compile(r'\bnew\s+[A-Za-z0-9_]+'), "C++ operator 'new' allocates memory dynamically on the heap"),
]

def analyze_robotics_code(content: str, language: str, file_path: str = "") -> Dict[str, Any]:
    lines = content.splitlines()
    publishers = []
    subscribers = []
    services = []
    realtime_issues = []
    framework = "generic"

    # Analyze ROS 2 (C++)
    if language in ["cpp", "c_cpp_header"]:
        for match in ROS2_PUBLISHER.finditer(content):
            publishers.append({"msg_type": match.group(1).strip(), "topic": match.group(2).strip()})
            framework = "ros2"
        for match in ROS2_SUBSCRIBER.finditer(content):
            subscribers.append({"msg_type": match.group(1).strip(), "topic": match.group(2).strip()})
            framework = "ros2"
        for match in ROS2_SERVICE.finditer(content):
            services.append({"srv_type": match.group(1).strip(), "service": match.group(2).strip()})
            framework = "ros2"

        # Check ROS 1 (C++)
        for match in ROS1_PUBLISHER.finditer(content):
            publishers.append({"msg_type": match.group(1).strip(), "topic": match.group(2).strip()})
            framework = "ros1"
        for match in ROS1_SUBSCRIBER.finditer(content):
            topic = match.group(2) if match.group(2) else match.group(1)
            subscribers.append({"msg_type": "unknown", "topic": topic.strip()})
            framework = "ros1"

    # Analyze Python (rospy / rclpy)
    elif language == "python":
        for match in PY_ROS2_PUB.finditer(content):
            publishers.append({"msg_type": match.group(1).strip(), "topic": match.group(2).strip()})
            framework = "ros2"
        for match in PY_ROS2_SUB.finditer(content):
            subscribers.append({"msg_type": match.group(1).strip(), "topic": match.group(2).strip()})
            framework = "ros2"
        for match in PY_ROS1_PUB.finditer(content):
            publishers.append({"msg_type": match.group(2).strip(), "topic": match.group(1).strip()})
            framework = "ros1"
        for match in PY_ROS1_SUB.finditer(content):
            subscribers.append({"msg_type": match.group(2).strip(), "topic": match.group(1).strip()})
            framework = "ros1"

    elif language == "arduino":
        framework = "arduino"

    # Check for Real-Time and Embedded violations line-by-line
    in_critical_section = False
    for line_idx, line in enumerate(lines, start=1):
        # Look for loop or ISR function headers
        lower = line.lower()
        if any(token in lower for token in ["isr(", "void loop(", "timer_callback", "control_loop", "update("]):
            in_critical_section = True

        for pattern, explanation in BLOCKING_CALLS:
            if pattern.search(line):
                realtime_issues.append({
                    "line": line_idx,
                    "type": "blocking_delay",
                    "severity": "WARNING" if not in_critical_section else "CRITICAL",
                    "code": line.strip(),
                    "issue": explanation,
                })

        for pattern, explanation in DYNAMIC_ALLOC_PATTERNS:
            if pattern.search(line) and in_critical_section:
                realtime_issues.append({
                    "line": line_idx,
                    "type": "dynamic_memory_allocation",
                    "severity": "HIGH",
                    "code": line.strip(),
                    "issue": explanation,
                })

    return {
        "framework": framework,
        "publishers": publishers,
        "subscribers": subscribers,
        "services": services,
        "realtime_issues": realtime_issues,
        "flags": [
            f"pub:{p['topic']}" for p in publishers
        ] + [
            f"sub:{s['topic']}" for s in subscribers
        ] + (["has_rt_issues"] if realtime_issues else []),
    }
