import os
import pathlib
from typing import Optional

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database path (stored in data/ for persistence if mounted, or local)
DB_PATH = os.environ.get("ROBORAG_DB_PATH", str(DATA_DIR / "robocode.db"))

# LLM Configurations
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "auto") # "auto", "openai", "groq", "ollama", "huggingface", "offline"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Search and chunking defaults
DEFAULT_CHUNK_SIZE = int(os.environ.get("ROBORAG_CHUNK_SIZE", 80))
DEFAULT_CHUNK_OVERLAP = int(os.environ.get("ROBORAG_CHUNK_OVERLAP", 15))
DEFAULT_TOP_K = int(os.environ.get("ROBORAG_TOP_K", 5))

# CORS Allowed Origins
CORS_ORIGINS = [
    "*",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
