"""Agent routes (/backend/agent_new, /backend/agent_execute, etc.)."""
import logging
import traceback

from bson.objectid import ObjectId
from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backend", tags=["agents"])


def _models():
    import api.models as m  # noqa: PLC0415
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
            return {"status": "400", "error": "Missing required fields: name, description, user_id"}

        agent_id = models.Agent.create(owner_id=user_id, name=name, description=description, task_type=task_type, config=config)
        if agent_id:
            return {"status": "200", "message": f"Agent '{name}' created", "data": {"agent_id": agent_id}}
        raise Exception("Failed to create agent")
    except Exception as exc:
        logger.error("create_agent: %s\n%s", exc, traceback.format_exc())
        return {"status": "500", "error": str(exc)}


@router.post("/agent_execute")
async def execute_agent(request: Request):
    try:
        models = _models()
        data = await request.json()
        agent_id = data.get("agent_id")
        user_message = data.get("user_message", "")
        user_id = data.get("user_id")

        if not agent_id:
            return {"status": "400", "error": "Missing required field: agent_id"}

        agent = models.Agent.get(agent_id)
        if not agent:
            return {"status": "404", "error": "Agent not found"}

        if agent.get("owner") != user_id:
            return {"status": "403", "error": "Unauthorized access to agent"}

        system_prompt = agent.get("system_prompt", agent.get("description", ""))
        config = agent.get("config", {})
        max_words = config.get("max_tokens", 1000) / 1.3

        from api import provider_ollama  # noqa: PLC0415
        try:
            provider_ollama.init_ollama()
        except Exception:
            pass

        result = provider_ollama.get_ollama_gpt_response(
            primer_message=system_prompt,
            user_message=user_message,
            max_words=int(max_words) if max_words else None,
        )

        if result.get("status") == "200":
            return {"status": "200", "data": {"response": result.get("res", ""), "token_usage": result.get("token", {}), "agent_id": agent_id, "agent_name": agent.get("name", "")}}
        return {"status": "500", "error": result.get("error", "Failed to execute agent")}
    except Exception as exc:
        logger.error("execute_agent: %s\n%s", exc, traceback.format_exc())
        return {"status": "500", "error": str(exc)}


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
            return {"status": "400", "error": "Missing required field: agent_id"}
        if not dataset_id:
            return {"status": "400", "error": "Missing required field: dataset_id"}
        if not selected_items:
            return {"status": "400", "error": "No items selected for analysis"}

        agent = models.Agent.get(agent_id)
        if not agent:
            return {"status": "404", "error": f"Agent not found with ID: {agent_id}"}

        if agent.get("owner") != user_id:
            return {"status": "403", "error": "Unauthorized access to agent"}

        if agent.get("task_type"):
            task = agent.get("task_type")

        system_prompt = agent.get("system_prompt", agent.get("description", ""))
        config = agent.get("config", {})
        max_words = config.get("max_tokens", 1000) / 1.3

        dataset = models.Dataset.get(ObjectId(dataset_id), True, False)
        if not dataset:
            return {"status": "404", "error": "Dataset not found"}

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
            return {"status": "400", "error": "No images found in selected items"}

        from api import provider_blip2, provider_ollama  # noqa: PLC0415

        blip2_result = provider_blip2.get_blip2_multimodal_response(
            primer_message="You are an expert image analyzer. Describe what you see in detail.",
            user_message="Provide a detailed description of this image.",
            images=images_base64,
            max_words=int(max_words) if max_words else 200,
        )

        if blip2_result.get("status") != "200":
            return {"status": blip2_result.get("status", "500"), "error": f"Blip2 error: {blip2_result.get('error')}"}

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
            return {"status": ollama_result.get("status", "500"), "error": f"Ollama error: {ollama_result.get('error')}"}

        return {
            "status": "200",
            "result": ollama_result.get("res", "").strip(),
            "blip2_description": blip2_text,
            "agent_name": agent.get("name", ""),
            "items_analyzed": len(items_processed),
            "token_usage": {"blip2": blip2_result.get("token", {}), "ollama": ollama_result.get("token", {})},
            "agent_id": agent_id,
        }
    except Exception as exc:
        logger.error("execute_agent_with_images: %s\n%s", exc, traceback.format_exc())
        return {"status": "500", "error": str(exc)}


@router.get("/agents")
async def get_agents(request: Request):
    try:
        models = _models()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return {"status": "400", "error": "Missing required parameter: user_id"}
        agents = models.Agent.get_all(user_id)
        return {"status": "200", "data": agents}
    except Exception as exc:
        logger.error("get_agents: %s\n%s", exc, traceback.format_exc())
        return {"status": "500", "error": str(exc)}


@router.post("/agent_delete")
async def delete_agent(request: Request):
    try:
        models = _models()
        data = await request.json()
        agent_id = data.get("agent_id")
        if not agent_id:
            return {"status": "400", "error": "Missing required parameter: agent_id"}
        success = models.Agent.delete(agent_id)
        if success:
            return {"status": "200", "message": "Agent deleted successfully"}
        return {"status": "500", "error": "Failed to delete agent"}
    except Exception as exc:
        logger.error("delete_agent: %s\n%s", exc, traceback.format_exc())
        return {"status": "500", "error": str(exc)}
