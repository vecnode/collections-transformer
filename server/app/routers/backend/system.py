"""System/debug routes (/backend/ollama/models, /backend/db/*)."""
import json
import logging
import traceback

from bson import json_util
from fastapi import APIRouter, Request

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


@router.get("/db/inspect")
async def inspect_database():
    try:
        from api import db  # noqa: PLC0415
        collection_names = db.list_collection_names()
        collections_data = []
        for coll_name in collection_names:
            collection = db[coll_name]
            count = collection.count_documents({})
            sample_doc = collection.find_one({})
            fields = list(sample_doc.keys()) if sample_doc else []
            collections_data.append({"name": coll_name, "count": count, "fields": fields, "has_sample": sample_doc is not None})
        return {"status": "200", "data": {"database_name": db.name, "collections": collections_data}}
    except Exception as exc:
        logger.error("inspect_database: %s\n%s", exc, traceback.format_exc())
        return {"status": "500", "error": str(exc)}


@router.get("/db/collection/{collection_name}")
async def get_collection_documents(collection_name: str, request: Request):
    try:
        from api import db  # noqa: PLC0415
        limit = int(request.query_params.get("limit", 50))
        skip = int(request.query_params.get("skip", 0))
        collection = db[collection_name]
        documents = list(collection.find({}).skip(skip).limit(limit))
        documents_json = json.loads(json_util.dumps(documents))
        total_count = collection.count_documents({})
        return {"status": "200", "data": {"collection": collection_name, "documents": documents_json, "total": total_count, "skip": skip, "limit": limit}}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}
