"""Labelset routes (/backend/labelset*)."""
import json
import logging

from bson.objectid import ObjectId
from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backend", tags=["labelsets"])


def _models():
    import api.models as m  # noqa: PLC0415
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

        return {"status": "200", "data": ls}
    except Exception as exc:
        logger.error("labelsets: %s", exc)
        return {"status": "500", "error": str(exc)}


@router.get("/labelset")
async def labelset(request: Request):
    try:
        models = _models()
        p = request.query_params
        labelset_id = ObjectId(p.get("labelset_id"))
        include_labels = bool(p.get("include_labels"))
        ls = models.Labelset.get(None, labelset_id, include_labels)
        return {"status": "200", "data": ls}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.get("/labelset_copy")
async def labelset_copy(request: Request):
    try:
        models = _models()
        p = request.query_params
        labelset_id = ObjectId(p.get("labelset_id"))
        owner_id = p.get("owner_id")
        new_name = p.get("name")
        existing = models.Labelset.get(None, labelset_id)
        new_id = models.Labelset.create(owner_id, existing["dataset_id"], existing["label_type"], new_name)
        models.Label.copy_all(labelset_id, new_id, None)
        return {"status": "200", "data": str(new_id)}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.get("/labelset_new")
async def labelset_new(request: Request):
    try:
        models = _models()
        p = request.query_params
        name = p.get("name")
        ltype = p.get("type")
        dataset_id = ObjectId(p.get("dataset_id"))
        analyser_id = ObjectId(p.get("analyser_id")) if p.get("analyser_id") else None
        owner_id = p.get("owner_id")
        new_id = models.Labelset.create(owner_id, dataset_id, ltype, name, analyser_id)
        return {"status": "200", "data": str(new_id)}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.get("/labelset_update")
async def labelset_update(request: Request):
    try:
        models = _models()
        p = request.query_params
        labelset_id = ObjectId(p.get("labelset_id"))
        update_data = json.loads(p.get("data"))
        models.Labelset.update(labelset_id, update_data, False)
        return {"status": "200", "message": f"Labelset {labelset_id} updated"}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.post("/labelset_delete")
async def labelset_delete(request: Request):
    try:
        models = _models()
        labelset_id = ObjectId(request.query_params.get("labelset_id"))
        models.Labelset.delete(labelset_id)
        return {"status": "200", "message": f"Labelset {labelset_id} deleted"}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}
