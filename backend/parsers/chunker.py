import re
from typing import List, Dict, Any

# Regex to detect function, method, struct, or class headers in C/C++, Python, Rust, Arduino
SYMBOL_REGEX = re.compile(
    r"^(?:\s*)(?:class\s+([A-Za-z0-9_]+)|"
    r"struct\s+([A-Za-z0-9_]+)|"
    r"def\s+([A-Za-z0-9_]+)\s*\(|"
    r"(?:void|int|bool|float|double|uint[0-9]+_t|int[0-9]+_t|auto|Status|rclcpp::[A-Za-z0-9_:]+)\s+([A-Za-z0-9_:]+)\s*\()",
    re.MULTILINE
)

def extract_symbol_name(lines: List[str]) -> str:
    for line in lines[:10]:
        match = SYMBOL_REGEX.search(line)
        if match:
            # Return first non-None captured group
            for group in match.groups():
                if group:
                    return group
    return ""

def chunk_file_content(
    content: str,
    chunk_size: int = 80,
    chunk_overlap: int = 15,
) -> List[Dict[str, Any]]:
    """
    Chunk code content with line number tracking and symbol detection.
    Default chunk size: 80 lines (ideal for code blocks and functions).
    Overlap: 15 lines.
    """
    lines = content.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return []

    # If the file is smaller than chunk_size, return a single chunk
    if total_lines <= chunk_size:
        symbol = extract_symbol_name(lines)
        return [{
            "chunk_id": 1,
            "start_line": 1,
            "end_line": total_lines,
            "content": content,
            "symbol_name": symbol,
        }]

    chunks = []
    chunk_id = 1
    step = max(1, chunk_size - chunk_overlap)

    for start_idx in range(0, total_lines, step):
        end_idx = min(start_idx + chunk_size, total_lines)
        chunk_lines = lines[start_idx:end_idx]
        symbol = extract_symbol_name(chunk_lines)
        chunk_text = "\n".join(chunk_lines)

        chunks.append({
            "chunk_id": chunk_id,
            "start_line": start_idx + 1,
            "end_line": end_idx,
            "content": chunk_text,
            "symbol_name": symbol,
        })
        chunk_id += 1

        if end_idx >= total_lines:
            break

    return chunks
