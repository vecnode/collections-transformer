"""Redis client management for FastAPI lifespan."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_redis: Optional[object] = None  # redis.asyncio.Redis


def get_redis():
    """Return the active Redis client (set during lifespan startup)."""
    return _redis


async def connect(url: str):
    """Connect to Redis; returns the client."""
    global _redis
    try:
        from redis.asyncio import Redis  # type: ignore
        _redis = await Redis.from_url(url, decode_responses=True)
        await _redis.ping()
        logger.info("Redis connection successful (%s)", url)
        return _redis
    except Exception as exc:
        logger.warning("Redis unavailable (%s) – caching and queuing disabled: %s", url, exc)
        _redis = None
        return None


async def disconnect() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        logger.info("Redis connection closed")
        _redis = None
