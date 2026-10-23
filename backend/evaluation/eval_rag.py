import time
import json
import sys
import os
import pathlib

# Ensure root workspace is on python path
WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from typing import List, Dict, Any
from backend.database import init_db
from backend.routes.api import index_directory, IndexRequest
from backend.retrieval.hybrid_retriever import retriever

# Curated Robotics RAG Benchmark Dataset
BENCHMARK_CASES = [
    {
        "id": "CASE-01",
        "category": "Control Systems",
        "query": "Where is the compute_pid loop implemented for velocity error?",
        "expected_file": "diffbot_controller.cpp",
        "expected_symbol": "compute_pid",
    },
    {
        "id": "CASE-02",
        "category": "ROS2 Communication",
        "query": "Show the subscriber callback for cmd_vel velocity topic",
        "expected_file": "diffbot_controller.cpp",
        "expected_symbol": "cmd_vel_callback",
    },
    {
        "id": "CASE-03",
        "category": "Embedded Firmware",
        "query": "Where is the encoder interrupt service routine ISR defined?",
        "expected_file": "motor_driver_arduino.ino",
        "expected_symbol": "encoder_isr",
    },
    {
        "id": "CASE-04",
        "category": "Kinematics & URDF",
        "query": "Find left wheel continuous joint and link in URDF description",
        "expected_file": "diffbot.urdf.xacro",
        "expected_symbol": "left_wheel_joint",
    },
    {
        "id": "CASE-05",
        "category": "ROS2 Launch",
        "query": "Where is the robot state publisher node configured in the launch file?",
        "expected_file": "diffbot_launch.py",
        "expected_symbol": "robot_state_publisher",
    },
    {
        "id": "CASE-06",
        "category": "Package Dependencies",
        "query": "Which dependencies are listed in the package xml specification?",
        "expected_file": "package.xml",
        "expected_symbol": "geometry_msgs",
    },
    {
        "id": "CASE-07",
        "category": "Control Systems",
        "query": "Where is the odometry publisher initialized and published?",
        "expected_file": "diffbot_controller.cpp",
        "expected_symbol": "publish_odometry",
    },
    {
        "id": "CASE-08",
        "category": "Embedded Firmware",
        "query": "How is non-blocking millis timer calculated in Arduino loop?",
        "expected_file": "motor_driver_arduino.ino",
        "expected_symbol": "loop",
    },
]

def run_evaluation(top_k: int = 5) -> Dict[str, Any]:
    # 1. Initialize and index sample robotics package
    init_db()
    examples_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "examples" / "diffbot_firmware"
    index_res = index_directory(IndexRequest(project_path=str(examples_dir)))

    results = []
    total_rr = 0.0
    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    total_latency_ms = 0.0

    for case in BENCHMARK_CASES:
        start_t = time.perf_counter()
        citations = retriever.retrieve(case["query"], top_k=top_k)
        latency = (time.perf_counter() - start_t) * 1000.0
        total_latency_ms += latency

        found_rank = None
        for rank, cit in enumerate(citations, start=1):
            file_match = case["expected_file"].lower() in cit["file_path"].lower()
            snippet_match = case["expected_symbol"].lower() in cit["snippet"].lower() or case["expected_symbol"].lower() in cit.get("symbol_name", "").lower()
            if file_match and snippet_match:
                found_rank = rank
                break

        rr = (1.0 / found_rank) if found_rank else 0.0
        total_rr += rr

        if found_rank == 1:
            hits_at_1 += 1
        if found_rank and found_rank <= 3:
            hits_at_3 += 1
        if found_rank and found_rank <= 5:
            hits_at_5 += 1

        results.append({
            "id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "expected_file": case["expected_file"],
            "expected_symbol": case["expected_symbol"],
            "rank": found_rank,
            "reciprocal_rank": round(rr, 3),
            "latency_ms": round(latency, 2),
            "status": "PASS" if found_rank else "FAIL",
        })

    num_cases = len(BENCHMARK_CASES)
    mrr = round(total_rr / num_cases, 4)
    avg_latency = round(total_latency_ms / num_cases, 2)
    h1 = round(hits_at_1 / num_cases * 100, 1)
    h3 = round(hits_at_3 / num_cases * 100, 1)
    h5 = round(hits_at_5 / num_cases * 100, 1)

    summary = {
        "total_test_cases": num_cases,
        "mrr": mrr,
        "hit_rate_at_1": f"{h1}%",
        "hit_rate_at_3": f"{h3}%",
        "hit_rate_at_5": f"{h5}%",
        "avg_retrieval_latency_ms": avg_latency,
        "test_results": results,
    }

    return summary

def generate_markdown_report(summary: Dict[str, Any]) -> str:
    md = [
        "# 📊 RoboCode RAG Benchmark Evaluation Report\n",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        f"- **Mean Reciprocal Rank (MRR):** `{summary['mrr']}`",
        f"- **Hit Rate @ 1:** `{summary['hit_rate_at_1']}`",
        f"- **Hit Rate @ 3:** `{summary['hit_rate_at_3']}`",
        f"- **Hit Rate @ 5:** `{summary['hit_rate_at_5']}`",
        f"- **Average Retrieval Latency:** `{summary['avg_retrieval_latency_ms']} ms`\n",
        "### Detailed Benchmark Cases\n",
        "| ID | Category | Query | Expected File | Rank | Latency | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in summary["test_results"]:
        status_badge = "✅ PASS" if r["status"] == "PASS" else "❌ FAIL"
        rank_str = str(r["rank"]) if r["rank"] else "Miss"
        md.append(f"| {r['id']} | {r['category']} | {r['query']} | `{r['expected_file']}` | {rank_str} | {r['latency_ms']} ms | {status_badge} |")
    return "\n".join(md)

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    summary = run_evaluation(top_k=5)
    report = generate_markdown_report(summary)
    
    # Save report to evaluation directory
    out_dir = pathlib.Path(__file__).parent
    (out_dir / "benchmark_report.md").write_text(report, encoding="utf-8")
    (out_dir / "benchmark_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    ascii_report = report.encode('ascii', errors='replace').decode('ascii')
    print(ascii_report)
    print(f"\nSaved report to: {out_dir / 'benchmark_report.md'}")
