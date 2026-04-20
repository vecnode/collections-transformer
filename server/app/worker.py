"""Background worker process.

Drains the 'queue:transforms' Redis list and executes transform jobs.
Run with:
    python -m app.worker
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys

_SERVER_DIR = os.path.dirname(os.path.dirname(__file__))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

from app.core.config import app_settings, configure_app_logging

configure_app_logging()
logger = logging.getLogger(__name__)

QUEUE_KEY = "queue:transforms"
JOB_KEY_PREFIX = "job:"


async def run_transform(payload: dict) -> dict:
    """Execute a transform operation.

    Extend this function to dispatch to domain logic based on
    payload["operation"].
    """
    operation = payload.get("operation", "noop")
    dataset_id = payload.get("dataset_id")
    logger.info("Running transform '%s' on dataset %s", operation, dataset_id)

    # Placeholder – real domain logic should dispatch through app.domain.models
    # or future app service modules.
    return {"operation": operation, "dataset_id": dataset_id, "result": "ok"}


async def main() -> None:
    from redis.asyncio import Redis  # type: ignore

    redis = await Redis.from_url(app_settings.redis_url, decode_responses=True)
    logger.info("Worker started – listening on '%s'", QUEUE_KEY)

    while True:
        try:
            item = await redis.brpop(QUEUE_KEY, timeout=5)
            if not item:
                continue

            _, job_id = item
            key = f"{JOB_KEY_PREFIX}{job_id}"
            await redis.hset(key, mapping={"status": "running"})
            logger.info("Processing job %s", job_id)

            try:
                raw_payload = await redis.hget(key, "payload")
                payload = json.loads(raw_payload) if raw_payload else {}
                result = await run_transform(payload)
                await redis.hset(key, mapping={"status": "done", "result": json.dumps(result)})
                logger.info("Job %s completed", job_id)
            except Exception as exc:
                logger.error("Job %s failed: %s", job_id, exc)
                await redis.hset(key, mapping={"status": "failed", "error": str(exc)})

        except Exception as exc:
            logger.error("Worker loop error: %s", exc)
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
