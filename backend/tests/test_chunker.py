import pytest
from backend.parsers.chunker import chunk_file_content, extract_symbol_name

def test_extract_symbol_name():
    lines = [
        "void PIDController::update() {",
        "    double error = setpoint - feedback;",
        "}"
    ]
    assert extract_symbol_name(lines) == "PIDController::update"

def test_chunk_file_content_small():
    code = "int a = 1;\nint b = 2;\n"
    chunks = chunk_file_content(code, chunk_size=50)
    assert len(chunks) == 1
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 2

def test_chunk_file_content_overlap():
    lines = [f"// line {i}" for i in range(1, 101)]
    code = "\n".join(lines)
    chunks = chunk_file_content(code, chunk_size=40, chunk_overlap=10)
    assert len(chunks) > 1
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 40
    assert chunks[1]["start_line"] == 31
