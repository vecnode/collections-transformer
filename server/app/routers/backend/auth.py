"""Authentication routes (/backend/auth/*, /backend/user/*)."""
import logging
import traceback

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backend", tags=["auth"])


def _models():
    import api.models as m  # noqa: PLC0415
    return m


@router.post("/auth/register")
async def register(request: Request):
    try:
        data = await request.json()
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not username or not email or not password:
            return {"status": "400", "error": "Username, email, and password are required"}

        if len(password) < 6:
            return {"status": "400", "error": "Password must be at least 6 characters"}

        models = _models()
        user_id, error = models.User.create_local_user(username, email, password)
        if error:
            return {"status": "400", "error": error}

        request.session["user_id"] = user_id
        request.session["username"] = username
        request.session["email"] = email
        models.User.record_connection(user_id, "register", True)

        return {"status": "200", "data": {"user_id": user_id, "username": username, "email": email}}
    except Exception as exc:
        logger.error("register: %s", exc)
        return {"status": "500", "error": str(exc)}


@router.post("/auth/login")
async def login(request: Request):
    try:
        data = await request.json()
        username_or_email = data.get("username", "").strip()
        password = data.get("password", "")

        if not username_or_email or not password:
            return {"status": "400", "error": "Username/email and password are required"}

        models = _models()
        user_id, username, email = models.User.authenticate_local_user(username_or_email, password)
        if not user_id:
            return {"status": "401", "error": "Invalid username/email or password"}

        request.session["user_id"] = user_id
        request.session["username"] = username
        request.session["email"] = email
        models.User.record_connection(user_id, "login", True)

        return {"status": "200", "data": {"user_id": user_id, "username": username, "email": email}}
    except Exception as exc:
        logger.error("login: %s", exc)
        return {"status": "500", "error": str(exc)}


@router.post("/auth/logout")
async def logout(request: Request):
    try:
        models = _models()
        user_id = request.session.get("user_id")
        if user_id:
            models.User.record_connection(user_id, "logout", False)
        request.session.clear()
        return {"status": "200", "message": "Logged out successfully"}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.get("/auth/verify")
async def verify_session(request: Request):
    try:
        models = _models()
        user_id = request.session.get("user_id")
        if not user_id:
            return {"status": "401", "authenticated": False, "error": "Not authenticated"}

        user = models.User.get_user_by_id(user_id)
        if not user:
            request.session.clear()
            return {"status": "401", "authenticated": False, "error": "User not found"}

        return {
            "status": "200",
            "authenticated": True,
            "data": {
                "user_id": user.get("user_id"),
                "username": user.get("username"),
                "email": user.get("email"),
                "role": user.get("role", ""),
                "affiliation": user.get("affiliation", ""),
            },
        }
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


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
            return {"status": "400", "error": "user_id is required"}

        should_update = event_type in ("login", "page_load", "page_visible")
        models.User.record_connection(user_id, event_type, should_update)
        return {"status": "200", "message": f"Connection recorded: {event_type}"}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.get("/user/last_connection")
async def get_last_connection(request: Request):
    try:
        models = _models()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return {"status": "400", "error": "user_id is required"}

        user_data = models.user_collection.find_one({"user_id": user_id})
        if user_data:
            last_connection = user_data.get("previous_connection") or user_data.get("last_connection")
            return {
                "status": "200",
                "data": {
                    "first_connection": user_data.get("first_connection").isoformat() if user_data.get("first_connection") else None,
                    "last_connection": last_connection.isoformat() if last_connection else None,
                    "last_event_type": user_data.get("last_event_type"),
                    "last_event_time": user_data.get("last_event_time").isoformat() if user_data.get("last_event_time") else None,
                },
            }
        return {"status": "200", "data": {"first_connection": None, "last_connection": None, "last_event_type": None, "last_event_time": None}}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.get("/user/profile")
async def get_user_profile(request: Request):
    try:
        models = _models()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return {"status": "400", "error": "user_id is required"}

        profile_data = models.User.get_user_profile(user_id)
        if profile_data.get("first_connection"):
            profile_data["first_connection"] = profile_data["first_connection"].isoformat()
        if profile_data.get("last_connection"):
            profile_data["last_connection"] = profile_data["last_connection"].isoformat()

        return {"status": "200", "data": profile_data}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.post("/user/profile")
async def update_user_profile(request: Request):
    try:
        models = _models()
        params = dict(request.query_params)
        user_id = params.get("user_id")
        role = params.get("role")
        affiliation = params.get("affiliation")

        if not user_id:
            return {"status": "400", "error": "user_id is required"}

        success = models.User.update_user_profile(user_id, role, affiliation)
        if success:
            return {"status": "200", "message": "Profile updated successfully"}
        return {"status": "400", "error": "No valid data provided for update"}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.get("/user/preferences")
async def get_user_preferences(request: Request):
    try:
        models = _models()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return {"status": "400", "error": "user_id is required"}

        preferences = models.User.get_user_preferences(user_id)
        return {"status": "200", "data": preferences}
    except Exception as exc:
        traceback.print_exc()
        return {"status": "500", "error": str(exc)}


@router.post("/user/preferences")
async def save_user_preferences(request: Request):
    try:
        models = _models()
        data = await request.json()
        user_id = data.get("user_id")
        text_provider = data.get("text_provider")

        if not user_id:
            return {"status": "400", "error": "user_id is required"}

        if text_provider and text_provider != "ollama":
            return {"status": "400", "error": "text_provider must be 'ollama'"}

        success, message = models.User.update_user_preferences(user_id, text_provider=text_provider)
        if success:
            return {"status": "200", "message": message, "data": models.User.get_user_preferences(user_id)}
        return {"status": "400", "error": message}
    except Exception as exc:
        traceback.print_exc()
        return {"status": "500", "error": str(exc)}
