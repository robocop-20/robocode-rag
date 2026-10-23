# 📊 RoboCode RAG Benchmark Evaluation Report

**Date:** 2026-10-23 06:44:57 UTC
- **Mean Reciprocal Rank (MRR):** `0.8542`
- **Hit Rate @ 1:** `75.0%`
- **Hit Rate @ 3:** `100.0%`
- **Hit Rate @ 5:** `100.0%`
- **Average Retrieval Latency:** `2.46 ms`

### Detailed Benchmark Cases

| ID | Category | Query | Expected File | Rank | Latency | Status |
|---|---|---|---|---|---|---|
| CASE-01 | Control Systems | Where is the compute_pid loop implemented for velocity error? | `diffbot_controller.cpp` | 1 | 3.3 ms | ✅ PASS |
| CASE-02 | ROS2 Communication | Show the subscriber callback for cmd_vel velocity topic | `diffbot_controller.cpp` | 2 | 2.55 ms | ✅ PASS |
| CASE-03 | Embedded Firmware | Where is the encoder interrupt service routine ISR defined? | `motor_driver_arduino.ino` | 1 | 1.94 ms | ✅ PASS |
| CASE-04 | Kinematics & URDF | Find left wheel continuous joint and link in URDF description | `diffbot.urdf.xacro` | 1 | 2.18 ms | ✅ PASS |
| CASE-05 | ROS2 Launch | Where is the robot state publisher node configured in the launch file? | `diffbot_launch.py` | 1 | 2.94 ms | ✅ PASS |
| CASE-06 | Package Dependencies | Which dependencies are listed in the package xml specification? | `package.xml` | 1 | 2.39 ms | ✅ PASS |
| CASE-07 | Control Systems | Where is the odometry publisher initialized and published? | `diffbot_controller.cpp` | 3 | 2.24 ms | ✅ PASS |
| CASE-08 | Embedded Firmware | How is non-blocking millis timer calculated in Arduino loop? | `motor_driver_arduino.ino` | 1 | 2.11 ms | ✅ PASS |