"""Category routes (/backend/category*, /backend/categories)."""
import logging

from bson.objectid import ObjectId
from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backend", tags=["categories"])


def _models():
    import api.models as m  # noqa: PLC0415
    return m


@router.get("/category")
@router.post("/category")
async def get_category(request: Request):
    try:
        models = _models()
        category_id = ObjectId(request.query_params.get("category_id"))
        category = models.Category.get(category_id)
        return {"status": "200", "data": category}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.get("/categories")
async def get_categories(request: Request):
    try:
        models = _models()
        user_id = request.query_params.get("user_id")
        categories_list = models.Category.get_all(user_id)
        return {"status": "200", "data": categories_list}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.post("/category_add")
async def create_category(request: Request):
    try:
        models = _models()
        params = dict(request.query_params)
        category_name = params.get("name")
        owner = params.get("user_id")
        category_id = models.category_collection.insert_one({"name": category_name, "owner": owner})
        return {"status": "200", "message": f"Category {category_name} created with ID {category_id}"}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.post("/category_delete")
async def category_delete(request: Request):
    try:
        models = _models()
        category_id = request.query_params.get("category_id")
        models.category_collection.delete_one({"_id": ObjectId(category_id)})
        return {"status": "200", "message": f"Category {category_id} has been deleted"}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}
