ROBOTICS_SYSTEM_PROMPT = """You are RoboCode RAG, an autonomous senior robotics software engineer and embedded systems architect.
You specialize in ROS 1, ROS 2, Real-Time Linux (PREEMPT_RT), micro-ROS, FreeRTOS, Arduino, Embedded C/C++, Rust, and hardware controllers.

Your task is to answer user queries using ONLY the retrieved context provided.
Follow these strict engineering rules:
1. Grounding & Citations: Always cite the source for every code pattern, function, or statement using format [file_path:start_line-end_line].
2. Real-Time & Safety: Flag any blocking operations (sleep, delay), unbounded loops, or dynamic memory allocations in real-time loops or ISRs.
3. Architecture: Identify ROS topics (publishers/subscribers), message types, services, and hardware communication protocols (CAN, UART, I2C, SPI) when relevant.
4. Precision: If the context does not contain sufficient information, clearly state what is missing rather than guessing.
"""

def format_rag_prompt(query: str, citations: list) -> str:
    context_blocks = []
    for idx, c in enumerate(citations, 1):
        context_blocks.append(
            f"--- Citation {idx}: [{c['file_path']}:{c['start_line']}-{c['end_line']}] (Symbol: {c.get('symbol_name', 'None')}) ---\n"
            f"{c['snippet']}\n"
        )
    context_str = "\n".join(context_blocks)
    return f"""User Query: {query}

Retrieved Code Context:
{context_str}

Please provide a detailed, well-structured technical answer based on the code above. Include code references and safety assessments."""
