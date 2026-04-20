"""System routes used by the current frontend."""
import logging
import traceback

from fastapi import APIRouter

from app.api_responses import error_response, success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backend", tags=["system"])


@router.get("/ollama/models")
async def get_ollama_models():
    try:
        from app.providers import provider_ollama  # noqa: PLC0415
        result = provider_ollama.list_ollama_models()
        if result.get("status") == "200":
            return success_response(data={"models": result.get("models", [])})
        return error_response(
            message=result.get("error", "Failed to fetch Ollama models"),
            status_code=int(result.get("status", "400")),
            data={"models": []},
        )
    except Exception as exc:
        logger.error("get_ollama_models: %s\n%s", exc, traceback.format_exc())
        return error_response(message=str(exc), status_code=500, data={"models": []})
