"""MongoDB connection management for FastAPI lifespan."""
import logging
from typing import Any

import gridfs
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_db: Any = None
_grid_fs: gridfs.GridFS | None = None


def connect(uri: str, database_name: str) -> tuple[MongoClient, Any, gridfs.GridFS]:
    """Connect to MongoDB and return (client, db, grid_fs)."""
    global _client, _db, _grid_fs
    try:
        logger.info("Connecting to MongoDB at %s", uri)
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        logger.info("MongoDB connection successful")

        _db = _client[database_name]
        if database_name not in _client.list_database_names():
            _db["init"].insert_one({"text": "init database"})
            logger.info("Initialized new database: %s", database_name)

        _grid_fs = gridfs.GridFS(_db)
        return _client, _db, _grid_fs

    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        logger.error("MongoDB connection failed: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected MongoDB error: %s", exc)
        raise


def disconnect() -> None:
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")


def get_client() -> MongoClient | None:
    return _client


def get_db() -> Any:
    return _db


def get_grid_fs() -> gridfs.GridFS | None:
    return _grid_fs
