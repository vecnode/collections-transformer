"""Agent routes used by the current frontend."""
import logging
import traceback

from bson.objectid import ObjectId
from fastapi import APIRouter, Request

from app.api_responses import error_response, success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backend", tags=["agents"])


def _models():
    import legacy_api.models as m  # noqa: PLC0415
    return m


@router.post("/agent_new")
async def create_agent(request: Request):
    try:
        models = _models()
        data = await request.json()
        name = data.get("name")
        description = data.get("description")
        task_type = data.get("task_type")
        user_id = data.get("user_id")
        config = data.get("config", None)

        if not all([name, description, user_id]):
            return error_response(message="Missing required fields: name, description, user_id", status_code=400)

        agent_id = models.Agent.create(owner_id=user_id, name=name, description=description, task_type=task_type, config=config)
        if agent_id:
            return success_response(message=f"Agent '{name}' created", status_code=201, data={"agent_id": agent_id})
        raise Exception("Failed to create agent")
    except Exception as exc:
        logger.error("create_agent: %s\n%s", exc, traceback.format_exc())
        return error_response(message=str(exc), status_code=500)


@router.post("/agent_execute_with_images")
async def execute_agent_with_images(request: Request):
    try:
        models = _models()
        data = await request.json()
        agent_id = data.get("agent_id")
        dataset_id = data.get("dataset_id")
        selected_items = data.get("selected_items", [])
        user_id = data.get("user_id")
        task = data.get("task", "Image Detection (text)")

        if not agent_id:
            return error_response(message="Missing required field: agent_id", status_code=400)
        if not dataset_id:
            return error_response(message="Missing required field: dataset_id", status_code=400)
        if not selected_items:
            return error_response(message="No items selected for analysis", status_code=400)

        agent = models.Agent.get(agent_id)
        if not agent:
            return error_response(message=f"Agent not found with ID: {agent_id}", status_code=404)

        if agent.get("owner") != user_id:
            return error_response(message="Unauthorized access to agent", status_code=403)

        if agent.get("task_type"):
            task = agent.get("task_type")

        system_prompt = agent.get("system_prompt", agent.get("description", ""))
        config = agent.get("config", {})
        max_words = config.get("max_tokens", 1000) / 1.3

        dataset = models.Dataset.get(ObjectId(dataset_id), True, False)
        if not dataset:
            return error_response(message="Dataset not found", status_code=404)

        images_base64 = []
        items_processed = []

        for item_id_str in selected_items:
            try:
                item_id = ObjectId(item_id_str)
                item = next((a for a in dataset.get("artworks", []) if a.get("_id") == item_id_str), None)
                if not item:
                    continue
                for content_item in item.get("content", []):
                    if content_item.get("content_type") == "image":
                        image_storage_id = content_item.get("content_value", {}).get("image_storage_id")
                        if image_storage_id:
                            try:
                                img_b64 = models.Item.getImage(item_id, image_storage_id)
                                images_base64.append(img_b64.decode("utf-8") if isinstance(img_b64, bytes) else img_b64)
                                items_processed.append(item_id_str)
                            except Exception:
                                continue
            except Exception:
                continue

        if not images_base64:
            return error_response(message="No images found in selected items", status_code=400)

        from legacy_api import provider_blip2, provider_ollama  # noqa: PLC0415

        blip2_result = provider_blip2.get_blip2_multimodal_response(
            primer_message="You are an expert image analyzer. Describe what you see in detail.",
            user_message="Provide a detailed description of this image.",
            images=images_base64,
            max_words=int(max_words) if max_words else 200,
        )

        if blip2_result.get("status") != "200":
            return error_response(
                message=f"Blip2 error: {blip2_result.get('error')}",
                status_code=int(blip2_result.get("status", "500")),
            )

        blip2_text = blip2_result.get("res", "")

        try:
            provider_ollama.init_ollama()
        except Exception:
            pass

        ollama_result = provider_ollama.get_ollama_gpt_response(
            primer_message=system_prompt,
            user_message=f"Based on the following image description, return only True or False.\n\nImage Description:\n{blip2_text}\n\nCriteria: {system_prompt}\n\nReturn only True or False.",
            max_words=50,
        )

        if ollama_result.get("status") != "200":
            return error_response(
                message=f"Ollama error: {ollama_result.get('error')}",
                status_code=int(ollama_result.get("status", "500")),
            )

        return success_response(
            data={
                "result": ollama_result.get("res", "").strip(),
                "blip2_description": blip2_text,
                "agent_name": agent.get("name", ""),
                "items_analyzed": len(items_processed),
                "token_usage": {"blip2": blip2_result.get("token", {}), "ollama": ollama_result.get("token", {})},
                "agent_id": agent_id,
            }
        )
    except Exception as exc:
        logger.error("execute_agent_with_images: %s\n%s", exc, traceback.format_exc())
        return error_response(message=str(exc), status_code=500)


@router.get("/agents")
async def get_agents(request: Request):
    try:
        models = _models()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return error_response(message="Missing required parameter: user_id", status_code=400)
        agents = models.Agent.get_all(user_id)
        return success_response(data=agents)
    except Exception as exc:
        logger.error("get_agents: %s\n%s", exc, traceback.format_exc())
        return error_response(message=str(exc), status_code=500)


@router.post("/agent_delete")
async def delete_agent(request: Request):
    try:
        models = _models()
        data = await request.json()
        agent_id = data.get("agent_id")
        if not agent_id:
            return error_response(message="Missing required parameter: agent_id", status_code=400)
        success = models.Agent.delete(agent_id)
        if success:
            return success_response(message="Agent deleted successfully")
        return error_response(message="Failed to delete agent", status_code=500)
    except Exception as exc:
        logger.error("delete_agent: %s\n%s", exc, traceback.format_exc())
        return error_response(message=str(exc), status_code=500)
