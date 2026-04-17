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

def get_ollama_multimodal_response(primer_message, user_message, images, max_words=None):
    """Handle multimodal requests with images using Ollama's API"""
    try:
        print("\n" + "=" * 80)
        print("OLLAMA MULTIMODAL API CALL")
        print("=" * 80)
        
        # Calculate num_predict based on max_words if provided
        num_predict = 1000
        if max_words:
            num_predict = int(max_words * 1.3)
        
        print(f"Model: {ollama_model_option}")
        print(f"Base URL: {ollama_base_url}")
        print(f"Max Words: {max_words}")
        print(f"Num Predict: {num_predict}")
        print(f"Images Count: {len(images)}")
        
        # Ollama's multimodal API format: images are passed separately, not in content array
        # For models that support images, we need to use images parameter
        messages = [
            {
                "role": "system",
                "content": primer_message
            }
        ]
        
        print(f"\n[SYSTEM PROMPT]\n{primer_message}\n")
        
        # Build user message content as string (Ollama requires string, not array)
        user_message_text = user_message if user_message else ""
        print(f"[USER MESSAGE]\n{user_message_text}\n")
        
        messages.append({
            "role": "user",
            "content": user_message_text
        })
        
        # Prepare images array for Ollama (base64 strings without data URI prefix)
        images_array = []
        for idx, image_data in enumerate(images):
            image_preview = image_data[:50] if len(image_data) > 50 else image_data
            print(f"[IMAGE {idx + 1}] Base64 length: {len(image_data)} chars, Preview: {image_preview}...")
            # Ollama expects raw base64 strings (no data URI prefix)
            # Ensure it's a clean base64 string
            if isinstance(image_data, bytes):
                image_data = image_data.decode('utf-8')
            # Remove data URI prefix if present
            if image_data.startswith('data:image'):
                image_data = image_data.split(',', 1)[1]
            images_array.append(image_data)
        
        # Ollama multimodal format: content is string, images are separate parameter
        payload = {
            "model": ollama_model_option,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": num_predict,
                "temperature": 0.8
            }
        }
        
        # Add images parameter (array of base64 strings)
        if images_array:
            payload["images"] = images_array
        
        print(f"\n[SENDING REQUEST TO OLLAMA]")
        print(f"Endpoint: {ollama_base_url}/api/chat")
        print(f"Payload keys: {list(payload.keys())}")
        print(f"Messages count: {len(messages)}")
        if "images" in payload:
            print(f"Images in payload: {len(payload['images'])} image(s)")
            print(f"First image length: {len(payload['images'][0])} chars")
            print(f"First image preview: {payload['images'][0][:100]}...")
        print(f"User message content type: {type(messages[-1]['content'])}")
        print(f"User message content: {messages[-1]['content'][:200]}...")
        print("-" * 80)
        
        response = requests.post(
            f"{ollama_base_url}/api/chat",
            json=payload,
            timeout=300  # 5 minute timeout for local inference
        )
        
        print(f"\n[OLLAMA RESPONSE STATUS]")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"ERROR: {response.text}")
            print("=" * 80)
            return {
                "status": "400",
                "error": f"Ollama API returned status {response.status_code}: {response.text}"
            }
        
        result = response.json()
        
        if "message" not in result or "content" not in result["message"]:
            print(f"ERROR: Unexpected response format")
            print(f"Response: {result}")
            print("=" * 80)
            return {
                "status": "400",
                "error": f"Unexpected response format from Ollama: {result}"
            }
        
        llm_end_time_ms = round(datetime.now().timestamp() * 1000)
        response_text = result["message"]["content"]
        
        print(f"\n[OLLAMA RESPONSE CONTENT]")
        print(f"Response Length: {len(response_text)} characters")
        print(f"Response Text:\n{response_text}\n")
        
        token_usage = {
            "prompt_tokens": result.get("prompt_eval_count", 0),
            "completion_tokens": result.get("eval_count", 0),
            "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
        }
        
        print(f"[TOKEN USAGE]")
        print(f"Prompt Tokens: {token_usage['prompt_tokens']}")
        print(f"Completion Tokens: {token_usage['completion_tokens']}")
        print(f"Total Tokens: {token_usage['total_tokens']}")
        print("=" * 80 + "\n")
        
        return {
            "status": "200",
            "res": response_text,
            "end": llm_end_time_ms,
            "token": token_usage
        }
    
    except requests.exceptions.RequestException as e:
        print("Network exception in get_ollama_multimodal_response")
        print(e)
        print(traceback.format_exc())
        return {
            "status": "400",
            "error": f"Network error connecting to Ollama: {str(e)}"
        }
    
    except Exception as e:
        print("exception in get_ollama_multimodal_response")
        print(e)
        print(traceback.format_exc())
        return {
            "status": "400",
            "error": str(e)
        }
