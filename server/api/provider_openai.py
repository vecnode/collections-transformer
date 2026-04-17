import os
from datetime import datetime
import openai

openai_model_option = None

def init_openai():
    """Initialize OpenAI configuration"""
    global openai_model_option
    
    os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY')
    os.environ['OPENAI_API_TYPE'] = os.environ.get('OPENAI_API_TYPE')
    openai_model_option = os.environ.get('OPENAI_MODEL_OPTION')

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

