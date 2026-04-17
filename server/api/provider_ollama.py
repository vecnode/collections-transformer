import logging
import traceback
from datetime import datetime

import requests
from config import settings

logger = logging.getLogger(__name__)

ollama_model_option = None
ollama_base_url = None

def init_ollama():
    """Initialize Ollama configuration"""
    global ollama_model_option, ollama_base_url
    
    ollama_model_option = settings.ollama_model_option
    ollama_base_url = settings.ollama_base_url
    
    # Test connection to Ollama
    try:
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("Ollama initialized successfully with model: %s", ollama_model_option)
        else:
            logger.warning("Ollama connection test returned status %s", response.status_code)
    except Exception as e:
        logger.warning("Could not connect to Ollama at %s: %s", ollama_base_url, e)

def list_ollama_models():
    """List all available Ollama models"""
    try:
        ollama_base_url = settings.ollama_base_url
        logger.info("Fetching Ollama models from: %s/api/tags", ollama_base_url)
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)

        logger.info("Ollama API response status: %s", response.status_code)
        
        if response.status_code == 200:
            data = response.json()
            logger.debug("Ollama API response data: %s", data)
            models = []
            if 'models' in data:
                for model in data['models']:
                    model_name = model.get('name', '')
                    if model_name:
                        models.append(model_name)
            logger.info("Extracted %s Ollama models", len(models))
            return {
                "status": "200",
                "models": models
            }
        else:
            logger.warning(
                "Ollama API returned non-200 status: %s, response: %s",
                response.status_code,
                response.text,
            )
            return {
                "status": "400",
                "error": f"Ollama API returned status {response.status_code}",
                "models": []
            }
    except requests.exceptions.RequestException as e:
        logger.error("Network error connecting to Ollama: %s", e)
        logger.debug(traceback.format_exc())
        return {
            "status": "400",
            "error": f"Network error connecting to Ollama: {str(e)}",
            "models": []
        }
    except Exception as e:
        logger.error("Exception in list_ollama_models: %s", e)
        logger.debug(traceback.format_exc())
        return {
            "status": "400",
            "error": str(e),
            "models": []
        }

def get_ollama_gpt_response(primer_message, user_message, max_words=None):
    """Get response from Ollama (local inference)"""
    try:
        # Calculate max_tokens based on max_words if provided
        # Ollama uses num_predict instead of max_tokens
        num_predict = 1000
        if max_words:
            # Roughly 1.3 tokens per word for English text
            num_predict = int(max_words * 1.3)
        
        messages = [
            {
                "role": "system",
                "content": primer_message
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
        
        payload = {
            "model": ollama_model_option,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": num_predict,
                "temperature": 0.8
            }
        }
        
        response = requests.post(
            f"{ollama_base_url}/api/chat",
            json=payload,
            timeout=300  # 5 minute timeout for local inference
        )
        
        if response.status_code != 200:
            return {
                "status": "400",
                "error": f"Ollama API returned status {response.status_code}: {response.text}"
            }
        
        result = response.json()
        
        if "message" not in result or "content" not in result["message"]:
            return {
                "status": "400",
                "error": f"Unexpected response format from Ollama: {result}"
            }
        
        llm_end_time_ms = round(datetime.now().timestamp() * 1000)
        response_text = result["message"]["content"]
        
        # Ollama token metadata uses a different shape than hosted chat APIs.
        # We'll estimate it or create a simple structure
        token_usage = {
            "prompt_tokens": result.get("prompt_eval_count", 0),
            "completion_tokens": result.get("eval_count", 0),
            "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
        }
        
        return {
            "status": "200",
            "res": response_text,
            "end": llm_end_time_ms,
            "token": token_usage
        }
    
    except requests.exceptions.RequestException as e:
        logger.error("Network exception in get_ollama_gpt_response: %s", e)
        logger.debug(traceback.format_exc())
        return {
            "status": "400",
            "error": f"Network error connecting to Ollama: {str(e)}"
        }
    
    except Exception as e:
        logger.exception("Exception in get_ollama_gpt_response")
        logger.debug(traceback.format_exc())
        return {
            "status": "400",
            "error": str(e)
        }

