"""System routes used by the current frontend."""
import logging
import traceback

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backend", tags=["system"])


@router.get("/ollama/models")
async def get_ollama_models():
    try:
        from api import provider_ollama  # noqa: PLC0415
        result = provider_ollama.list_ollama_models()
        if result.get("status") == "200":
            return {"status": "200", "data": {"models": result.get("models", [])}}
        return {"status": result.get("status", "400"), "error": result.get("error", "Failed to fetch Ollama models"), "data": {"models": []}}
    except Exception as exc:
        logger.error("get_ollama_models: %s\n%s", exc, traceback.format_exc())
        return {"status": "500", "error": str(exc), "data": {"models": []}}
