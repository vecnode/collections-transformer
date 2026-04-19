"""Shared API state for the FastAPI runtime.

The FastAPI app initializes these globals during lifespan startup so legacy
model modules under api.models can keep importing `db` and `grid_fs`.
"""

from __future__ import annotations

from typing import Any

from pymongo import MongoClient

client: MongoClient | None = None
db: Any = None
grid_fs: Any = None
UPLOAD_FOLDER = "/cache"

