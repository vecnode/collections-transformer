"""Analysis history routes (/backend/analysis/*, /backend/item)."""
import logging

from bson.objectid import ObjectId
from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backend", tags=["analysis"])


def _models():
    import api.models as m  # noqa: PLC0415
    return m


@router.post("/analysis/save")
async def save_analysis(request: Request):
    try:
        models = _models()
        data = await request.json()
        user_id = data.get("user_id")
        dataset_id = data.get("dataset_id")

        if not all([user_id, dataset_id]):
            return {"status": "400", "error": "Missing required fields"}

        analysis_id = models.AnalysisHistory.create(
            user_id=user_id,
            dataset_id=dataset_id,
            selected_items=data.get("selected_items", []),
            chat_messages=data.get("chat_messages", []),
            analysis_summary=data.get("analysis_summary", {}),
            agent_id=data.get("agent_id"),
        )
        return {"status": "200", "analysis_id": analysis_id}
    except Exception as exc:
        logger.error("save_analysis: %s", exc)
        return {"status": "500", "error": str(exc)}


@router.get("/analysis/history")
async def get_analysis_history(request: Request):
    try:
        models = _models()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return {"status": "400", "error": "Missing user_id"}

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

        return {"status": "200", "data": analyses}
    except Exception as exc:
        logger.error("get_analysis_history: %s", exc)
        return {"status": "500", "error": str(exc)}


@router.post("/analysis/delete")
async def delete_analysis(request: Request):
    try:
        models = _models()
        data = await request.json()
        analysis_id = data.get("analysis_id")
        if not analysis_id:
            return {"status": "400", "error": "Missing analysis_id"}
        success = models.AnalysisHistory.delete(analysis_id)
        if success:
            return {"status": "200", "message": "Analysis deleted successfully"}
        return {"status": "500", "error": "Failed to delete analysis"}
    except Exception as exc:
        return {"status": "500", "error": str(exc)}


@router.get("/item")
async def get_item(request: Request):
    try:
        models = _models()
        item_id = ObjectId(request.query_params.get("item_id"))
        item = models.Item.get(item_id)
        formatted_item = models.Item.getFullItem(item, False)
        return {"status": "200", "data": formatted_item}
    except Exception as exc:
        logger.error("get_item: %s", exc)
        return {"status": "500", "error": str(exc)}
