"""FastAPI application entrypoint.

Startup order matters:
1. Connect to MongoDB
2. Connect to Redis (optional)
3. Initialize ML providers (optional)
4. Register routers
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import TYPE_CHECKING
from contextlib import asynccontextmanager

if TYPE_CHECKING:
    from fastapi import FastAPI

# Ensure the server/ directory is on sys.path so app modules are importable.
_SERVER_DIR = os.path.dirname(os.path.dirname(__file__))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

from app.core.config import app_settings, configure_app_logging
from app.api_responses import error_response

configure_app_logging()
logger = logging.getLogger(__name__)

# Track which model variant is active.
_active_model: str = "dual"


@asynccontextmanager
async def lifespan(app):
    """Startup / shutdown lifecycle for FastAPI."""
    # ------------------------------------------------------------------
    # 1. MongoDB – must succeed before any model code is imported
    # ------------------------------------------------------------------
    from app.infra import mongodb  # noqa: PLC0415

    _client, _db, _ = mongodb.connect(
        app_settings.mongodb_uri, app_settings.mongodb_database
    )

    # ------------------------------------------------------------------
    # 1b. Optional legacy migration flag (disabled by default)
    # ------------------------------------------------------------------
    if app_settings.migrate_legacy_on_startup:
        logger.warning(
            "MIGRATE_LEGACY_ON_STARTUP=true, but in-app auto-migration is disabled. "
            "Run migration scripts manually."
        )

    # ------------------------------------------------------------------
    # 2. Redis (optional)
    # ------------------------------------------------------------------
    from app.infra import redis_client  # noqa: PLC0415
    await redis_client.connect(app_settings.redis_url)

    # ------------------------------------------------------------------
    # 3. ML providers (optional)
    # ------------------------------------------------------------------
    try:
        from app.providers import llm_modelling  # noqa: PLC0415
        llm_modelling.init(_active_model)
    except Exception as exc:
        logger.warning("ML provider init skipped: %s", exc)

    logger.info("Application startup complete")
    yield

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------
    await redis_client.disconnect()
    mongodb.disconnect()
    logger.info("Application shutdown complete")


def create_app(model: str = "dual") -> "FastAPI":
    global _active_model
    _active_model = model

    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.exceptions import RequestValidationError
    from starlette.middleware.sessions import SessionMiddleware

    from app.routers.v1 import router as v1_router
    from app.routers.backend import router as backend_router

    application = FastAPI(
        title="Collections Transformer API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Session middleware (must be added before CORS)
    application.add_middleware(
        SessionMiddleware,
        secret_key=app_settings.secret_key,
        max_age=86400,  # 24 hours
        https_only=False,
        same_site="lax",
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Canonical contract: all backend routes are available under /api/v1/*.
    application.include_router(v1_router)
    application.include_router(backend_router, prefix="/api/v1")

    @application.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException):
        details = exc.detail if not isinstance(exc.detail, str) else None
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        return error_response(
            message=message,
            status_code=exc.status_code,
            details=details,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        return error_response(
            message="Request validation failed",
            status_code=422,
            code="validation_error",
            details=exc.errors(),
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception):
        logger.exception("Unhandled application error")
        return error_response(
            message="Internal server error",
            status_code=500,
            code="internal_server_error",
        )

    return application


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", default="dual")
    parser.add_argument("-p", "--port", type=int, default=app_settings.api_port)
    parser.add_argument("--reload", action="store_true", default=False)
    args, _ = parser.parse_known_args()

    app = create_app(args.model)
    uvicorn.run(
        app,
        host=app_settings.api_host,
        port=args.port,
        reload=args.reload,
    )


# Module-level app instance for `uvicorn app.main:app` invocations.
app = create_app()
