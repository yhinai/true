from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cbc.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Correct by Construction")
    origins_env = os.environ.get("CBC_CORS_ORIGINS", "*")
    origins = [o.strip() for o in origins_env.split(",") if o.strip()] or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app
