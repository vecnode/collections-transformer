"""Transform job queue endpoints for /api/v1/transforms.

Long-running transforms are enqueued in Redis so the HTTP request returns
immediately with a job_id.  A background worker (server/app/worker.py) drains
the queue and writes results back to Redis.
"""
import json
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.infra.redis_client import get_redis
from app.schemas.transforms import TransformJobStatus, TransformRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transforms", tags=["transforms"])

QUEUE_KEY = "queue:transforms"
JOB_KEY_PREFIX = "job:"


@router.post("", status_code=202)
async def create_transform(payload: TransformRequest):
    """Enqueue a transform job and return its job_id."""
    redis = get_redis()
    if not redis:
        raise HTTPException(status_code=503, detail="Queue unavailable – Redis not connected")

    job_id = str(uuid4())
    job_data = {
        "status": "queued",
        "payload": payload.model_dump_json(),
    }
    await redis.hset(f"{JOB_KEY_PREFIX}{job_id}", mapping=job_data)
    await redis.lpush(QUEUE_KEY, job_id)
    logger.info("Transform job %s enqueued", job_id)
    return {"job_id": job_id, "status": "queued"}


@router.get("/{job_id}", response_model=TransformJobStatus)
async def get_transform_status(job_id: str):
    """Poll the status of a previously enqueued transform job."""
    redis = get_redis()
    if not redis:
        raise HTTPException(status_code=503, detail="Queue unavailable – Redis not connected")

    job = await redis.hgetall(f"{JOB_KEY_PREFIX}{job_id}")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return TransformJobStatus(job_id=job_id, **job)
