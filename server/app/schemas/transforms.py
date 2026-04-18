"""Pydantic schemas for transform jobs."""
from typing import Any
from pydantic import BaseModel


class TransformRequest(BaseModel):
    dataset_id: str
    operation: str
    params: dict[str, Any] = {}


class TransformJobStatus(BaseModel):
    job_id: str
    status: str
    payload: str | None = None
    result: str | None = None
    error: str | None = None
