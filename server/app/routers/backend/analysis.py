"""Analysis history and item routes used by the current frontend."""
import logging

from bson.objectid import ObjectId
from fastapi import APIRouter, Request

from app.api_responses import error_response, success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backend", tags=["analysis"])


def _models():
    import legacy_api.models as m  # noqa: PLC0415
    return m


@router.post("/analysis/save")
async def save_analysis(request: Request):
    try:
        models = _models()
        data = await request.json()
        user_id = data.get("user_id")
        dataset_id = data.get("dataset_id")

        if not all([user_id, dataset_id]):
            return error_response(message="Missing required fields", status_code=400)

        analysis_id = models.AnalysisHistory.create(
            user_id=user_id,
            dataset_id=dataset_id,
            selected_items=data.get("selected_items", []),
            chat_messages=data.get("chat_messages", []),
            analysis_summary=data.get("analysis_summary", {}),
            agent_id=data.get("agent_id"),
        )
        return success_response(data={"analysis_id": analysis_id}, status_code=201)
    except Exception as exc:
        logger.error("save_analysis: %s", exc)
        return error_response(message=str(exc), status_code=500)


@router.get("/analysis/history")
async def get_analysis_history(request: Request):
    try:
        models = _models()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return error_response(message="Missing user_id", status_code=400)

        analyses = models.AnalysisHistory.get_all(user_id)
        for analysis in analyses:
            try:
                analysis["agent_name"] = "Unknown"
                if analysis.get("agent_id"):
                    agent = models.Agent.get(analysis["agent_id"])
                    analysis["agent_name"] = agent.get("name", "Unknown") if agent else "Unknown"
                elif analysis.get("analyser_name"):
                    analysis["agent_name"] = analysis.get("analyser_name")

                dataset = models.Dataset.get(analysis["dataset_id"])
                analysis["dataset_name"] = dataset.get("name", "Unknown") if dataset else "Unknown"
            except Exception:
                analysis["agent_name"] = "Unknown"
                analysis["dataset_name"] = "Unknown"

        return success_response(data=analyses)
    except Exception as exc:
        logger.error("get_analysis_history: %s", exc)
        return error_response(message=str(exc), status_code=500)


@router.post("/analysis/delete")
async def delete_analysis(request: Request):
    try:
        models = _models()
        data = await request.json()
        analysis_id = data.get("analysis_id")
        if not analysis_id:
            return error_response(message="Missing analysis_id", status_code=400)
        success = models.AnalysisHistory.delete(analysis_id)
        if success:
            return success_response(message="Analysis deleted successfully")
        return error_response(message="Failed to delete analysis", status_code=500)
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


@router.get("/item")
async def get_item(request: Request):
    try:
        models = _models()
        item_id = ObjectId(request.query_params.get("item_id"))
        item = models.Item.get(item_id)
        formatted_item = models.Item.getFullItem(item, False)
        return success_response(data=formatted_item)
    except Exception as exc:
        logger.error("get_item: %s", exc)
        return error_response(message=str(exc), status_code=500)


@router.get("/item_image")
async def get_item_image(request: Request):
    try:
        models = _models()
        item_id = request.query_params.get("item_id")
        image_storage_id = request.query_params.get("image_storage_id")

        if not item_id or not image_storage_id:
            return error_response(message="item_id and image_storage_id are required", status_code=400)

        image_data = models.Item.getImage(item_id, image_storage_id)
        return success_response(data=image_data.decode("utf-8") if isinstance(image_data, bytes) else image_data)
    except Exception as exc:
        logger.error("get_item_image: %s", exc)
        return error_response(message=str(exc), status_code=500)
