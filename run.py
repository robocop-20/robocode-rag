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

    # Workers: Render free tier has 512 MB RAM – keep 1 worker.
    # Override via WEB_CONCURRENCY for paid tiers.
    workers = int(os.environ.get("WEB_CONCURRENCY", 1))

    print("==================================================")
    print(" RoboCode RAG — Robotics & Embedded Systems AI")
    print(f" Listening on http://{host}:{port}")
    print(f" Environment: {env}  |  Workers: {workers}")
    print("==================================================")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
        proxy_headers=True,
        forwarded_allow_ips="*",
        access_log=True,
        timeout_keep_alive=75,          # Render uses 60 s idle timeout; stay above it
        timeout_graceful_shutdown=30,    # Drain in-flight requests on SIGTERM
    )

