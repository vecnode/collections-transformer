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
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure the server/ directory is on sys.path so `api` and `config` are importable.
_SERVER_DIR = os.path.dirname(os.path.dirname(__file__))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

from app.core.config import app_settings, configure_app_logging
from app.api_responses import error_response

configure_app_logging()
logger = logging.getLogger(__name__)

# Track which model variant is active.
_active_model: str = "dual"


def _auto_migrate_database(_db):
    """
    Auto-migrate SQLite/JSON data to MongoDB if MongoDB is empty.
    Called during application startup.
    """
    try:
        # Fast path: seeded/populated MongoDB should skip all heavy startup work.
        existing_datasets = _db["dataset"].count_documents({})
        if existing_datasets > 0:
            logger.info("MongoDB already populated (%d datasets), skipping SQLite export/migration", existing_datasets)
            return

        root_dir = Path(_SERVER_DIR).parent
        scripts_dir = root_dir / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))

        db_sqlite = root_dir / "server" / "db" / "db.sqlite"
        json_dir = root_dir / "server" / "db" / "sqlite2json"

        if db_sqlite.exists():
            from export_sqlite_to_json import export_sqlite_to_json  # noqa: PLC0415, E402

            exported = export_sqlite_to_json()
            if exported:
                logger.info("SQLite export completed from %s", db_sqlite)
            else:
                logger.warning("SQLite export failed from %s", db_sqlite)

        if not json_dir.exists():
            logger.warning("No JSON export directory found at %s", json_dir)
            return
        
        json_files_found = list(json_dir.glob("*.json"))
        if not json_files_found:
            logger.warning("No JSON export files found in %s", json_dir)
            return

        source_dataset_count = 0
        dataset_json = json_dir / "dataset.json"
        if dataset_json.exists():
            import json  # noqa: PLC0415

            with dataset_json.open("r", encoding="utf-8") as f:
                source_dataset_count = len(json.load(f))

        target_dataset_count = existing_datasets
        if target_dataset_count >= source_dataset_count and source_dataset_count > 0:
            logger.info(
                "MongoDB dataset count (%d) matches/exceeds source (%d), skipping migration",
                target_dataset_count,
                source_dataset_count,
            )
            return

        logger.info(
            "Starting migration because MongoDB dataset count (%d) is behind source (%d)",
            target_dataset_count,
            source_dataset_count,
        )

        from migrate_sqlite_to_mongodb import MigrationManager  # noqa: PLC0415, E402
        
        manager = MigrationManager()
        manager.client = _db.client
        manager.db = _db

        manager.create_backup()
        manager.validate_json_files()
        manager.reset_target_collections()
        manager.import_collections()
        manager.update_references()
        manager.refactor_collections()
        manager.verify_migration()
        manager.print_summary()
        
        logger.info("✓ Auto-migration completed successfully")
        
    except Exception as exc:
        logger.warning("Auto-migration skipped or failed (this is okay for fresh installs): %s", exc)
        # Don't fail startup if migration fails - allow app to start fresh


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
    # 1b. Auto-migrate SQLite/JSON data if needed
    # ------------------------------------------------------------------
    _auto_migrate_database(_db)

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
