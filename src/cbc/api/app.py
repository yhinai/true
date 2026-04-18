from __future__ import annotations

from fastapi import FastAPI

from cbc.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Correct by Construction")
    app.include_router(router)
    return app
