from __future__ import annotations

import logging
import os

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from cbc.api.routes import router

_LOG = logging.getLogger(__name__)

_DEFAULT_CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
_LOCALHOST_HOSTS = {"127.0.0.1", "localhost", "::1"}

# Routes that MUST bypass auth entirely.
_PUBLIC_PATHS = {"/health"}


def _load_cors_origins() -> list[str]:
    raw = os.environ.get("CBC_CORS_ORIGINS")
    if raw is None:
        return list(_DEFAULT_CORS_ORIGINS)
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or list(_DEFAULT_CORS_ORIGINS)


_bearer_scheme = HTTPBearer(auto_error=False)


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> None:
    """Enforce bearer-token auth when ``CBC_API_TOKEN`` is configured.

    When the token env var is unset, requests are allowed through (the
    startup check warns operators running on non-localhost hosts).
    """
    if request.url.path in _PUBLIC_PATHS:
        return
    token = os.environ.get("CBC_API_TOKEN")
    if not token:
        return
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if credentials.credentials != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _warn_if_unsafe_bind(host: str | None) -> None:
    """Log a WARNING if bound to a non-localhost host without auth."""
    if os.environ.get("CBC_API_TOKEN"):
        return
    if host is None or host in _LOCALHOST_HOSTS:
        return
    _LOG.warning(
        "CBC_API_TOKEN is unset and server is bound to %s; "
        "bind to 127.0.0.1 or set CBC_API_TOKEN for remote access.",
        host,
    )


def create_app(*, host: str | None = None) -> FastAPI:
    app = FastAPI(title="Correct by Construction", dependencies=[Depends(require_auth)])
    origins = _load_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(router)
    _warn_if_unsafe_bind(host)
    return app
