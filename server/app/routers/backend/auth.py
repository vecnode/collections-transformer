"""User profile and preference routes."""
import logging

from fastapi import APIRouter, Request

from app.api_responses import error_response, success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backend", tags=["auth"])


def _models():
    import legacy_api.models as m  # noqa: PLC0415
    return m


@router.post("/user/record_connection")
async def record_user_connection(request: Request):
    try:
        models = _models()
        params = dict(request.query_params)
        user_id = params.get("user_id")
        event_type = params.get("event_type", "login")

        if not user_id:
            body = await request.json()
            user_id = body.get("user_id")
            event_type = body.get("event_type", "login")

        if not user_id:
            return error_response(message="user_id is required", status_code=400)

        should_update = event_type in ("login", "page_load", "page_visible")
        models.User.record_connection(user_id, event_type, should_update)
        return success_response(message=f"Connection recorded: {event_type}")
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


@router.get("/user/last_connection")
async def get_last_connection(request: Request):
    try:
        models = _models()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return error_response(message="user_id is required", status_code=400)

        user_data = models.user_collection.find_one({"user_id": user_id})
        if user_data:
            last_connection = user_data.get("previous_connection") or user_data.get("last_connection")
            return success_response(
                data={
                    "first_connection": user_data.get("first_connection").isoformat() if user_data.get("first_connection") else None,
                    "last_connection": last_connection.isoformat() if last_connection else None,
                    "last_event_type": user_data.get("last_event_type"),
                    "last_event_time": user_data.get("last_event_time").isoformat() if user_data.get("last_event_time") else None,
                }
            )
        return success_response(data={"first_connection": None, "last_connection": None, "last_event_type": None, "last_event_time": None})
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


@router.get("/user/profile")
async def get_user_profile(request: Request):
    try:
        models = _models()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return error_response(message="user_id is required", status_code=400)

        profile_data = models.User.get_user_profile(user_id)
        if profile_data.get("first_connection"):
            profile_data["first_connection"] = profile_data["first_connection"].isoformat()
        if profile_data.get("last_connection"):
            profile_data["last_connection"] = profile_data["last_connection"].isoformat()

        return success_response(data=profile_data)
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


@router.post("/user/profile")
async def update_user_profile(request: Request):
    try:
        models = _models()
        params = dict(request.query_params)
        user_id = params.get("user_id")
        role = params.get("role")
        affiliation = params.get("affiliation")

        if not user_id:
            return error_response(message="user_id is required", status_code=400)

        success = models.User.update_user_profile(user_id, role, affiliation)
        if success:
            return success_response(message="Profile updated successfully")
        return error_response(message="No valid data provided for update", status_code=400)
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


@router.get("/user/preferences")
async def get_user_preferences(request: Request):
    try:
        models = _models()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return error_response(message="user_id is required", status_code=400)

        preferences = models.User.get_user_preferences(user_id)
        return success_response(data=preferences)
    except Exception as exc:
        logger.exception("get_user_preferences")
        return error_response(message=str(exc), status_code=500)


@router.post("/user/preferences")
async def save_user_preferences(request: Request):
    try:
        models = _models()
        data = await request.json()
        user_id = data.get("user_id")
        text_provider = data.get("text_provider")

        if not user_id:
            return error_response(message="user_id is required", status_code=400)

        if text_provider and text_provider != "ollama":
            return error_response(message="text_provider must be 'ollama'", status_code=400)

        success, message = models.User.update_user_preferences(user_id, text_provider=text_provider)
        if success:
            return success_response(message=message, data=models.User.get_user_preferences(user_id))
        return error_response(message=message, status_code=400)
    except Exception as exc:
        logger.exception("save_user_preferences")
        return error_response(message=str(exc), status_code=500)
