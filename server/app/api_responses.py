from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def _error_code_from_status(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase.lower().replace(" ", "_")
    except ValueError:
        return "error"


def success_response(
    *,
    data: Any = None,
    message: str | None = None,
    status_code: int = 200,
    **extra: Any,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "ok": True,
        "status_code": status_code,
        # Transitional compatibility for existing frontend callers.
        "status": str(status_code),
    }

    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data

    payload.update(extra)
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))


def error_response(
    *,
    message: str,
    status_code: int,
    code: str | None = None,
    details: Any = None,
    data: Any = None,
    **extra: Any,
) -> JSONResponse:
    error_payload: dict[str, Any] = {
        "code": code or _error_code_from_status(status_code),
        "message": message,
    }
    if details is not None:
        error_payload["details"] = details

    payload: dict[str, Any] = {
        "ok": False,
        "status_code": status_code,
        # Transitional compatibility for existing frontend callers.
        "status": str(status_code),
        "message": message,
        "error": error_payload,
    }

    if data is not None:
        payload["data"] = data

    payload.update(extra)
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))