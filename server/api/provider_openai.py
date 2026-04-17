import os
from datetime import datetime
import openai
from openai import OpenAI

openai_model_option = None
llm_client = None

def init_openai():
    """Initialize OpenAI configuration"""
    global openai_model_option, llm_client
    
    os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY')
    os.environ['OPENAI_API_TYPE'] = os.environ.get('OPENAI_API_TYPE')
    openai_model_option = os.environ.get('OPENAI_MODEL_OPTION')
    
    llm_client = OpenAI(
        api_key=os.environ['OPENAI_API_KEY']  
    )

def get_openai_gpt_response(primer_message, user_message, max_words=None):
    """Get response from OpenAI GPT"""
    try:
        # Calculate max_tokens based on max_words if provided
        max_tokens = 1000
        if max_words:
            # Roughly 1.3 tokens per word for English text
            max_tokens = int(max_words * 1.3)
        
        chat_settings = {
            "model": openai_model_option,
            "max_tokens": max_tokens,
            "temperature": 0.8
        }

        body = {
            "model":
            chat_settings["model"],
            "messages": [{
                "role": "system",
                "content": primer_message
            }, {
                "role": "user",
                "content": user_message
            }]
        }

        completion = openai.chat.completions.create(
            model=chat_settings["model"],
            messages=body["messages"],
            max_tokens=chat_settings["max_tokens"],
            temperature=chat_settings["temperature"])

        llm_end_time_ms = round(datetime.now().timestamp() * 1000)
        response_text = completion.choices[0].message.content
        token_usage = completion.usage

        return {
            "status":"200",
            "res":response_text,
            "end":llm_end_time_ms, 
            "token":token_usage 
        }
    
    except Exception as e:
        print("exception in get_openai_gpt_response")
        print(e)

def get_openai_multimodal_response(primer_message, user_message, images, max_words=None):
    """Handle multimodal requests with images using OpenAI's API"""
    try:
        # Calculate max_tokens based on max_words if provided
        max_tokens = 1000
        if max_words:
            # Roughly 1.3 tokens per word for English text
            max_tokens = int(max_words * 1.3)
        
        # Use GPT-4o model for multimodal requests (replaces deprecated gpt-4-vision-preview)
        model_name = openai_model_option #"gpt-4o" #if "gpt-4" in openai_model_option else openai_model_option
        
        chat_settings = {
            "model": model_name,
            "max_tokens": max_tokens,
            "temperature": 0.8
        }

        # Prepare messages with images
        messages = [{
            "role": "system",
            "content": primer_message
        }]

        # Create user message with text and images
        user_content = []
        
        # Add text content
        if user_message:
            user_content.append({
                "type": "text",
                "text": user_message
            })
        
        # Add image content
        for i, image_data in enumerate(images):
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_data}",
                    "detail": "low"
                }
            })

        messages.append({
            "role": "user",
            "content": user_content
        })

        completion = openai.chat.completions.create(
            model=chat_settings["model"],
            messages=messages,
            max_tokens=chat_settings["max_tokens"],
            temperature=chat_settings["temperature"])

        llm_end_time_ms = round(datetime.now().timestamp() * 1000)
        response_text = completion.choices[0].message.content
        token_usage = completion.usage

        return {
            "status":"200",
            "res":response_text,
            "end":llm_end_time_ms, 
            "token":token_usage 
        }
    
    except Exception as e:
        print("exception in get_openai_multimodal_response")
        print(e)
        return {
            "status":"500",
            "error": str(e)
        }

