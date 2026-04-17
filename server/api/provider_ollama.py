import os
import requests
import traceback
from datetime import datetime

ollama_model_option = None
ollama_base_url = None

def init_ollama():
    """Initialize Ollama configuration"""
    global ollama_model_option, ollama_base_url
    
    ollama_model_option = os.environ.get('OLLAMA_MODEL_OPTION', 'gemma3:27b')
    ollama_base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Test connection to Ollama
    try:
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print(f"Ollama initialized successfully with model: {ollama_model_option}")
        else:
            print(f"Warning: Ollama connection test returned status {response.status_code}")
    except Exception as e:
        print(f"Warning: Could not connect to Ollama at {ollama_base_url}: {e}")

def list_ollama_models():
    """List all available Ollama models"""
    try:
        ollama_base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        print(f"Fetching Ollama models from: {ollama_base_url}/api/tags")
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        
        print(f"Ollama API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Ollama API response data: {data}")
            models = []
            if 'models' in data:
                for model in data['models']:
                    model_name = model.get('name', '')
                    if model_name:
                        models.append(model_name)
            print(f"Extracted models: {models}")
            return {
                "status": "200",
                "models": models
            }
        else:
            print(f"Ollama API returned non-200 status: {response.status_code}, response: {response.text}")
            return {
                "status": "400",
                "error": f"Ollama API returned status {response.status_code}",
                "models": []
            }
    except requests.exceptions.RequestException as e:
        print(f"Network error connecting to Ollama: {e}")
        print(traceback.format_exc())
        return {
            "status": "400",
            "error": f"Network error connecting to Ollama: {str(e)}",
            "models": []
        }
    except Exception as e:
        print(f"Exception in list_ollama_models: {e}")
        print(traceback.format_exc())
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
        
        # Ollama doesn't provide token usage in the same format as OpenAI
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
        print("Network exception in get_ollama_gpt_response")
        print(e)
        print(traceback.format_exc())
        return {
            "status": "400",
            "error": f"Network error connecting to Ollama: {str(e)}"
        }
    
    except Exception as e:
        print("exception in get_ollama_gpt_response")
        print(e)
        print(traceback.format_exc())
        return {
            "status": "400",
            "error": str(e)
        }

