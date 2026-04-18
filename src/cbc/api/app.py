from __future__ import annotations

from pathlib import Path

from .routes import build_router

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover - exercised when fastapi is installed
    FastAPI = None  # type: ignore[assignment]


def create_app(artifacts_root: Path | str = "artifacts"):
    if FastAPI is None:
        raise RuntimeError("fastapi is not installed; install fastapi to run the API server.")

    app = FastAPI(
        title="Correct by Construction Sidecar API",
        description="Thin run/review/benchmark read API from local artifact JSON files.",
        version="0.1.0",
    )
    app.include_router(build_router(artifacts_root))
    return app
