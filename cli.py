#!/usr/bin/env python3
"""
RoboCode RAG CLI — Command line interface for robotics developers.
Usage:
    python cli.py query "Where is the PID loop?"
    python cli.py index ./examples/diffbot_firmware
    python cli.py audit ./examples/diffbot_firmware/diffbot_controller.cpp
    python cli.py eval
    python cli.py status
"""

import sys
import os
import argparse
import asyncio
import pathlib

# Ensure root is on path
ROOT_DIR = pathlib.Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.database import init_db, get_db_stats
from backend.routes.api import index_directory, IndexRequest
from backend.retrieval.hybrid_retriever import retriever
from backend.parsers.robotics_analyzer import analyze_robotics_code
from backend.parsers.language import detect_language
from backend.generation.llm_client import llm_client

def cmd_status(args):
    init_db()
    stats = get_db_stats()
    print("=== RoboCode RAG Index Telemetry ===")
    print(f"Total Files Indexed:   {stats['total_files']}")
    print(f"Total Chunks:          {stats['total_chunks']}")
    print(f"Total Robotics Nodes:  {stats['total_robotics_nodes']}")
    print("Languages Breakdown:")
    for lang, count in stats["languages"].items():
        print(f"  - {lang:15s}: {count}")

def cmd_index(args):
    init_db()
    path = args.path
    print(f"Indexing robotics codebase at: {path} ...")
    req = IndexRequest(project_path=str(pathlib.Path(path).resolve()))
    res = index_directory(req)
    print(f"[OK] {res['message']}")

def cmd_query(args):
    init_db()
    query = args.query
    top_k = args.top_k
    print(f"\n[QUERY] Querying: \"{query}\" (Top-{top_k}) ...\n")
    citations = retriever.retrieve(query, top_k=top_k)
    if not citations:
        print("[ERROR] No relevant code chunks found. Did you index your project first?")
        return

    # Generate answer
    answer = asyncio.run(llm_client.generate_answer(query, citations))
    print(answer)
    print("\n" + "=" * 60)
    print("CITATIONS & CODE REFERENCES:")
    for i, c in enumerate(citations, 1):
        print(f"[{i}] {c['file_path']}:{c['start_line']}-{c['end_line']} (Relevance: {c['relevance_score']}%)")

def cmd_audit(args):
    file_path = pathlib.Path(args.file)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    content = file_path.read_text(encoding="utf-8", errors="ignore")
    lang = detect_language(str(file_path))
    analysis = analyze_robotics_code(content, lang, str(file_path))

    print(f"\n[AUDIT] Static Robotics Audit for: {file_path.name} ({lang.upper()})")
    print("=" * 60)
    print(f"Framework:      {analysis['framework'].upper()}")
    print(f"Publishers:     {len(analysis['publishers'])}")
    for p in analysis['publishers']:
        print(f"  - Topic: {p['topic']} ({p['msg_type']})")
    print(f"Subscribers:    {len(analysis['subscribers'])}")
    for s in analysis['subscribers']:
        print(f"  - Topic: {s['topic']} ({s['msg_type']})")
    print(f"Real-Time Issues: {len(analysis['realtime_issues'])}")
    for issue in analysis['realtime_issues']:
        print(f"  - [Line {issue['line']}] {issue['severity']}: {issue['issue']}")
        print(f"    Code: {issue['code']}")

def cmd_eval(args):
    from backend.evaluation.eval_rag import run_evaluation, generate_markdown_report
    print("Running RoboCode RAG automated benchmark evaluation...")
    summary = run_evaluation(top_k=5)
    report = generate_markdown_report(summary)
    ascii_report = report.encode('ascii', errors='replace').decode('ascii')
    print(ascii_report)

def main():
    parser = argparse.ArgumentParser(description="RoboCode RAG Command Line Interface")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Show database index telemetry")
    p_status.set_defaults(func=cmd_status)

    # index
    p_index = subparsers.add_parser("index", help="Index a robotics directory")
    p_index.add_argument("path", help="Path to project directory")
    p_index.set_defaults(func=cmd_index)

    # query
    p_query = subparsers.add_parser("query", help="Query the codebase with hybrid RAG")
    p_query.add_argument("query", help="Natural language query or code symbol")
    p_query.add_argument("--top-k", type=int, default=3, help="Number of citations to retrieve")
    p_query.set_defaults(func=cmd_query)

    # audit
    p_audit = subparsers.add_parser("audit", help="Audit a robotics file for ROS pub/sub and RT safety")
    p_audit.add_argument("file", help="File to audit")
    p_audit.set_defaults(func=cmd_audit)

    # eval
    p_eval = subparsers.add_parser("eval", help="Run automated evaluation benchmark")
    p_eval.set_defaults(func=cmd_eval)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
