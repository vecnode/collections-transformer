"""Dataset CRUD routes."""
import json
import logging
import traceback

from bson.objectid import ObjectId
from fastapi import APIRouter, Form, Request

from app.api_responses import error_response, success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backend", tags=["datasets"])


def _models():
    import app.domain.models as m  # noqa: PLC0415
    return m


@router.get("/dataset")
@router.post("/dataset")
async def get_dataset(request: Request):
    try:
        models = _models()
        dataset_id = request.query_params.get("dataset_id")
        if not dataset_id:
            return error_response(message="dataset_id is required", status_code=400)
        include_items = bool(request.query_params.get("include_items"))
        dataset = models.Dataset.get(ObjectId(dataset_id), include_items, False)
        return success_response(data=dataset)
    except Exception as exc:
        logger.error("get_dataset: %s", exc)
        return error_response(message=str(exc), status_code=500)


@router.get("/datasets")
async def get_datasets(request: Request):
    try:
        models = _models()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return error_response(message="user_id is required", status_code=400)
        datasets_list = models.Dataset.get_all(user_id)
        return success_response(data=datasets_list)
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


@router.post("/dataset_new")
async def dataset_new(
    request: Request,
    dataset_name: str = Form(...),
):
    try:
        models = _models()
        params = dict(request.query_params)
        owner_id = params.get("owner_id")
        dataset_type = params.get("dataset_type")
        image_upload_type = params.get("image_upload_type")

        if not owner_id or not dataset_type:
            return error_response(message="owner_id and dataset_type are required", status_code=400)

        form = await request.form()

        if dataset_type == "text":
            text_file = form.get("text_file")
            dataset_id = models.Dataset.create(owner_id, dataset_type, dataset_name, text_file, None, None, None)
            return success_response(message="Dataset has been created", status_code=201, data={"dataset_id": str(dataset_id)})

        elif dataset_type == "image":
            if image_upload_type == "image_file":
                image_files = form.getlist("image_file")
                dataset_id = models.Dataset.create(owner_id, dataset_type, dataset_name, None, image_files, None, image_upload_type)
                return success_response(message="Dataset has been created", status_code=201, data={"dataset_id": str(dataset_id)})
            else:
                image_file = form.get("image_file")
                dataset_id, error_links = models.Dataset.create(owner_id, dataset_type, dataset_name, None, image_file, None, image_upload_type)
                return success_response(message="Dataset has been created", status_code=201, data={"dataset_id": str(dataset_id), "error_links": error_links})

        elif dataset_type == "textimage":
            if image_upload_type == "image_file":
                text_file = form.get("text_file")
                image_files = form.getlist("image_file")
                dataset_id = models.Dataset.create(owner_id, dataset_type, dataset_name, text_file, image_files, None, image_upload_type)
                error_links = []
            else:
                text_image_file = form.get("text_image_file")
                dataset_id, error_links = models.Dataset.create(owner_id, dataset_type, dataset_name, None, None, text_image_file, image_upload_type)
            return success_response(message="Dataset has been created", status_code=201, data={"dataset_id": str(dataset_id), "error_links": error_links})

        return error_response(message="Unknown dataset_type", status_code=400)
    except Exception as exc:
        logger.error("dataset_new: %s\n%s", exc, traceback.format_exc())
        return error_response(message=str(exc), status_code=500)


@router.post("/dataset_delete")
async def dataset_delete(request: Request):
    try:
        models = _models()
        dataset_id = request.query_params.get("dataset_id")
        if not dataset_id:
            return error_response(message="dataset_id is required", status_code=400)
        models.Dataset.delete(dataset_id)
        return success_response(message=f"Dataset {dataset_id} has been deleted")
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


@router.get("/dataset_status")
async def dataset_status(request: Request):
    try:
        models = _models()
        dataset_id = request.query_params.get("dataset_id")
        if not dataset_id:
            return error_response(message="dataset_id is required", status_code=400)
        cursor = models.dataset_collection.find({"_id": ObjectId(dataset_id)}, {"status": 1, "artwork_count": 1})
        dataset = list(cursor)[0]
        return success_response(data={"id": dataset_id, "status": dataset["status"]})
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


@router.get("/dataset_update")
async def dataset_update(request: Request):
    try:
        models = _models()
        dataset_id = request.query_params.get("dataset_id")
        if not dataset_id:
            return error_response(message="dataset_id is required", status_code=400)
        data = json.loads(request.query_params.get("data"))
        models.Dataset.update(dataset_id, data)
        return success_response(message=f"Dataset {dataset_id} updated")
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)
