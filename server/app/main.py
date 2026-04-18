"""FastAPI application entrypoint.

Startup order matters:
1. Connect to MongoDB (sets api.db / api.grid_fs globals used by api.models)
2. Connect to Redis (optional – gracefully degraded if unavailable)
3. Initialize ML providers (optional)
4. Register routers
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from contextlib import asynccontextmanager

# Ensure the server/ directory is on sys.path so `api` and `config` are importable.
_SERVER_DIR = os.path.dirname(os.path.dirname(__file__))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

from app.core.config import app_settings, configure_app_logging

configure_app_logging()
logger = logging.getLogger(__name__)

# Track which model variant is active (used by /backend/model_source).
_active_model: str = "dual"


@asynccontextmanager
async def lifespan(app):
    """Startup / shutdown lifecycle for FastAPI."""
    # ------------------------------------------------------------------
    # 1. MongoDB – must succeed before any model code is imported
    # ------------------------------------------------------------------
    from app.infra import mongodb  # noqa: PLC0415
    import api  # noqa: PLC0415 – triggers api/__init__.py stubs only

    _client, _db, _grid_fs = mongodb.connect(
        app_settings.mongodb_uri, app_settings.mongodb_database
    )
    # Inject into the api module globals so existing models keep working.
    api.client = _client
    api.db = _db
    api.grid_fs = _grid_fs

    # ------------------------------------------------------------------
    # 2. Redis (optional)
    # ------------------------------------------------------------------
    from app.infra import redis_client  # noqa: PLC0415
    await redis_client.connect(app_settings.redis_url)

    # ------------------------------------------------------------------
    # 3. ML providers (optional)
    # ------------------------------------------------------------------
    try:
        from api import llm_modelling  # noqa: PLC0415
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

    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
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

    application.include_router(v1_router)
    application.include_router(backend_router)

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
