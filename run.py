import os
import sys
import uvicorn

if __name__ == "__main__":
    # Ensure current directory is on python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # Render supplies PORT environment variable dynamically
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    env = os.environ.get("ROBORAG_ENV", "production")
    reload = env == "development"

    print(f"==================================================")
    print(f" RoboCode RAG - Robotics & Embedded Systems AI")
    print(f" Listening on http://{host}:{port}")
    print(f" Environment: {env}")
    print(f"==================================================")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
