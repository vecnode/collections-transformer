from fastapi import APIRouter
from .auth import router as auth_router
from .datasets import router as datasets_router
from .categories import router as categories_router
from .labelsets import router as labelsets_router
from .agents import router as agents_router
from .analysis import router as analysis_router
from .system import router as system_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(datasets_router)
router.include_router(categories_router)
router.include_router(labelsets_router)
router.include_router(agents_router)
router.include_router(analysis_router)
router.include_router(system_router)
