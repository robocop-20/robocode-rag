# 🤖 RoboCode RAG

> **Autonomous AI Coding Assistant & RAG Engine for Robotics & Embedded Systems**  
> Tailored for ROS 1, ROS 2, Real-Time Linux (PREEMPT_RT), micro-ROS, FreeRTOS, Arduino, Embedded C/C++, and Rust.

---

## 🚀 Key Capabilities

- **Hybrid Lexical & Semantic Retrieval**: Combines SQLite FTS5 (BM25) with high-speed subword TF-IDF vector similarity using Reciprocal Rank Fusion (RRF).
- **Robotics & Real-Time Static Analysis**: Automatically discovers ROS publishers, subscribers, services, action clients, and detects real-time violations (e.g. blocking `delay()` / `sleep()` inside control loops, `new` / `malloc()` in ISRs).
- **Structure-Aware Code Chunking**: Intelligent code boundary preservation with function/class symbol extraction and exact `[file:start_line-end_line]` citation mapping.
- **Multi-Provider LLM Engine**: Seamlessly integrates with **Groq**, **OpenAI**, **Ollama**, **HuggingFace**, and includes a **Built-In Offline Synthesizer** that works out-of-the-box without requiring any external API keys or GPU.
- **Cyberpunk Dark-Mode Web Dashboard**: Served directly from the backend container—featuring real-time queries, file drag-and-drop ingestion, interactive code citations, and a live static audit tool.
- **Render.com Cloud Native**: One-click deployment with `render.yaml` Blueprint or containerized `Dockerfile`.

---

## 🌐 Deploying to Render.com

This repository is pre-configured for **Render.com** free or paid tiers.

### Method 1: Deploy with `render.yaml` (Recommended Blueprint)
1. Push this repository to GitHub or GitLab.
2. In the [Render Dashboard](https://dashboard.render.com/):
   - Click **New +** → **Blueprint**.
   - Connect your repository.
   - Render will detect [`render.yaml`](file:///d:/RAG/render.yaml) automatically.
   - Click **Apply**.
3. Render will build and deploy the web service automatically with health checks at `/health`.

### Method 2: Manual Web Service Setup
1. In Render, select **New +** → **Web Service**.
2. Connect your Git repository.
3. Choose runtime:
   - **Python 3**:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python run.py`
   - *OR* **Docker**:
     - Render uses the provided [`Dockerfile`](file:///d:/RAG/Dockerfile) automatically.
4. **Environment Variables** (Optional):
   - `PORT`: Automatically set by Render (defaults to `10000`).
   - `ROBORAG_ENV`: `production`
   - `GROQ_API_KEY`: *(Optional)* For ultra-fast Llama 3 inference.
   - `OPENAI_API_KEY`: *(Optional)* For GPT-4o-mini inference.

---

## 🛠️ Local Development & Running

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python run.py
```
Open your browser to: **`http://localhost:8000`**

### 3. Run the Test Suite
```bash
python -m pytest backend/tests -v
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Health check for Render uptime monitoring |
| `/api/index` | `POST` | Index a project directory on the server |
| `/api/upload` | `POST` | Upload a `.zip` or code files directly via web browser |
| `/api/query` | `POST` | Query the codebase with RAG and citations |
| `/api/analyze-robotics` | `POST` | Run static safety and ROS topic audit on a snippet |
| `/api/status` | `GET` | Get telemetry on indexed files, chunks, and nodes |
| `/api/clear` | `POST` | Clear all database records and vector stores |
| `/docs` | `GET` | Interactive Swagger API documentation |

---

## 📂 Architecture

```
d:/RAG/
├── Dockerfile                   # Multi-stage production container for Render
├── render.yaml                  # Render Blueprint configuration
├── run.py                       # Application runner reading $PORT
├── requirements.txt             # Project dependencies
├── backend/
│   ├── main.py                  # FastAPI application with CORS and static UI mount
│   ├── config.py                # Environment and path configurations
│   ├── database.py              # SQLite FTS5 schema & persistence
│   ├── parsers/
│   │   ├── language.py          # Language detector (ROS, C++, Python, Arduino, URDF)
│   │   ├── chunker.py           # Smart chunker with symbol extraction
│   │   └── robotics_analyzer.py # Static analyzer for ROS pub/sub & RT safety
│   ├── retrieval/
│   │   ├── vector_store.py      # TF-IDF subword vector store (0 heavy deps)
│   │   └── hybrid_retriever.py  # BM25 + Vector RRF hybrid ranker
│   ├── generation/
│   │   ├── llm_client.py        # Groq/OpenAI/Ollama/Offline synthesizer
│   │   └── prompts.py           # Robotics system prompts
│   ├── routes/
│   │   ├── api.py               # Core API endpoints
│   │   └── health.py            # /health check
│   └── tests/                   # Complete test suite (11 passing tests)
├── frontend/
│   └── static/                  # Responsive Cyberpunk Dark-Mode SPA
│       ├── index.html
│       ├── style.css
│       └── app.js
└── examples/
    └── diffbot_firmware/        # ROS2 sample package for verification
```

---

## 📜 License
Apache-2.0. Built with pride for robotics and embedded systems engineers.
