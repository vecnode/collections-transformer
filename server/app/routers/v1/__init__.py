from fastapi import APIRouter
from .health import router as health_router
from .transforms import router as transforms_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(transforms_router)
