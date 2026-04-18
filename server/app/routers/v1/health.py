"""Health and readiness endpoints for /api/v1/."""
import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "ok"}


@router.get("/readiness")
async def readiness():
    """Readiness probe – checks MongoDB and Redis."""
    from app.infra import mongodb, redis_client

    checks: dict[str, str] = {}

    # MongoDB check
    try:
        if mongodb._client:
            mongodb._client.admin.command("ping")
            checks["mongodb"] = "ok"
        else:
            checks["mongodb"] = "not connected"
    except Exception as exc:
        checks["mongodb"] = f"error: {exc}"

    # Redis check
    try:
        redis = redis_client.get_redis()
        if redis:
            await redis.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "not connected"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}
