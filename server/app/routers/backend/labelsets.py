"""Labelset and label update routes used by the current frontend."""
import json
import logging

from bson.objectid import ObjectId
from fastapi import APIRouter, Request

from app.api_responses import error_response, success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backend", tags=["labelsets"])


def _models():
    import app.domain.models as m  # noqa: PLC0415
    return m


@router.get("/labelsets")
async def labelsets(request: Request):
    try:
        models = _models()
        p = request.query_params
        include_labels = bool(p.get("include_labels"))
        include_names = bool(p.get("include_names", True))
        include_count = bool(p.get("include_count", True))
        dataset_id = ObjectId(p.get("dataset_id")) if p.get("dataset_id") else None
        label_type = p.get("label_type") or None
        user_id = p.get("user_id") or None

        if dataset_id is not None or label_type is not None:
            ls = models.Labelset.get_all(user_id, dataset_id, label_type, include_labels, include_names, include_count)
        else:
            ls = models.Labelset.all(user_id, include_labels, include_names, include_count)

        return success_response(data=ls)
    except Exception as exc:
        logger.error("labelsets: %s", exc)
        return error_response(message=str(exc), status_code=500)


@router.post("/labelset_delete")
async def labelset_delete(request: Request):
    try:
        models = _models()
        labelset_id_raw = request.query_params.get("labelset_id")
        if not labelset_id_raw:
            return error_response(message="labelset_id is required", status_code=400)
        labelset_id = ObjectId(labelset_id_raw)
        models.Labelset.delete(labelset_id)
        return success_response(message=f"Labelset {labelset_id} deleted")
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


def _parse_item_listing_id(raw_id: str) -> tuple[str, str, str]:
    label_subtype = None
    listing_id = raw_id

    if "-checkbox-" in raw_id:
        label_subtype, listing_id = raw_id.split("-checkbox-", 1)

    parts = listing_id.split("-")
    if len(parts) < 4 or parts[0] != "artwork":
        raise ValueError("Unsupported item identifier format")

    item_id = parts[1]
    content_type = parts[2]
    return item_id, content_type, label_subtype


@router.get("/update_label")
@router.post("/update_label")
async def update_label(request: Request):
    try:
        models = _models()
        params = request.query_params
        labelset_id = params.get("labelset_id")
        raw_id = params.get("id")

        if not labelset_id or not raw_id:
            return error_response(message="labelset_id and id are required", status_code=400)

        item_id, content_type, label_subtype = _parse_item_listing_id(raw_id)
        labelset = models.Labelset.get(None, labelset_id)
        label_type = labelset.get("label_type")

        options = {}
        if label_subtype is not None:
            options["label_subtype"] = label_subtype
        if "checked" in params:
            options["ticked"] = params.get("checked") == "true"
        if "exclude" in params:
            options["exclude"] = str(params.get("exclude")).lower()
        if "score" in params:
            score = params.get("score")
            options["score"] = score if score == "empty" else int(score)
        if "rationale" in params:
            options["rationale"] = params.get("rationale")
        if "highlight" in params:
            options["highlight"] = json.loads(params.get("highlight"))

        models.Label.update(
            label_type,
            ObjectId(labelset_id),
            ObjectId(item_id),
            raw_id,
            content_type,
            options,
        )
        return success_response(message="Label updated")
    except ValueError as exc:
        return error_response(message=str(exc), status_code=400)
    except Exception as exc:
        logger.error("update_label: %s", exc)
        return error_response(message=str(exc), status_code=500)
