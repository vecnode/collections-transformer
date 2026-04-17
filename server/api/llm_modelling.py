


import os
from datetime import datetime
import re
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"
os.environ["PYTORCH_USE_CUDA_DSA"] = "1"

import math
import traceback
import random
import re
import copy

import numpy as np

from sklearn.metrics import mean_absolute_error, root_mean_squared_error, precision_recall_fscore_support

from . import provider_openai as provider_openai
from . import provider_blip2 as provider_blip2




def init(model):
    
    global model_source

    model_source=model
    
    env_value = os.environ.get("ENVIRONMENT")
    if env_value is None:
        env_value = "default"
    os.environ["ENVIRONMENT"] = env_value
    
    # Initialize all providers - they will all be available
    # User can choose text provider (Ollama/OpenAI) in Settings
    # Blip2 is always used for images
    try:
        from . import provider_ollama as provider_ollama
        provider_ollama.init_ollama()
        print("Ollama initialized (available for text tasks)")
    except Exception as e:
        print(f"Warning: Could not initialize Ollama: {e}")
    
    try:
        provider_openai.init_openai()
        print("OpenAI initialized (available for text tasks)")
    except Exception as e:
        print(f"Warning: Could not initialize OpenAI: {e}")
    
    try:
        provider_blip2.init_blip2()
        print("Blip2 initialized (always used for image tasks)")
    except Exception as e:
        print(f"Warning: Could not initialize Blip2: {e}")

    print("======================================================")
    print("================= SERVER INITIALISED =================")
    print("Model Source: " + model_source)
    print("Providers: Ollama (text) + Blip2 (images)")
    print("======================================================")



def get_model_baseline(prompt_examples,items_for_inference,analyser,labels,dataset):

  #Get fake "random" predictions based on example distribution
  if (analyser['analyser_type'] == "binary"):
    pos_examples = [example for example in prompt_examples if str(example['label']) == "1"]
    prob = len(pos_examples)/len(prompt_examples)
    prob_dist = [prob, 1-prob]
    random_preds = random.choices(["positive","negative"],prob_dist,k=len(items_for_inference))
    predictions = [{item["_id"]:random_preds[index]} for index, item in enumerate(items_for_inference)]

    trained_example_ids = [example['_id'] for example in prompt_examples]

  elif (analyser['analyser_type'] == "score"):
    positive_examples = [example for example in prompt_examples if str(example['label']) == "1"]
    prob = len(positive_examples)/len(prompt_examples)
    
    predictions = [{item["_id"]: 1 if random.random() < prob else 0} for item in items_for_inference]
    trained_example_ids = [example['_id'] for example in prompt_examples]

  elif (analyser['analyser_type'] == "opinion"):
    positive_examples = [example for example in prompt_examples if str(example['label']) == "1"]
    prob = len(positive_examples)/len(prompt_examples)
    
    default_opinions = []
    for i in range(len(items_for_inference)):
      if random.random() < prob:
        default_opinions.append("This is a good example of the pattern we are looking for.")
      else:
        default_opinions.append("This is not a good example of the pattern we are looking for.")
    
    predictions = [{item["_id"]: default_opinions[index]} for index, item in enumerate(items_for_inference)]
    trained_example_ids = [example['_id'] for example in prompt_examples]

  else:

    return None

  try:
    accuracy = compute_accuracy(labels,dataset,trained_example_ids,predictions,analyser['analyser_type'],analyser['analyser_format'], True)
  
  except Exception as e:
    print(e)
    return None
  
  return accuracy



def use_model(prompt,prompt_examples,item_indices,items_for_inference, analyser):
  try:
    prediction_results = make_predictions(prompt,prompt_examples,item_indices,items_for_inference, analyser['analyser_type'], analyser['analyser_format'])
    return prediction_results
  
  except Exception as e:
    print (e)



def create_user_prompt(inference_examples, analyser_type, analyser_format):
  try:

    prompt = f"\nNow always give a total of exactly {len(inference_examples)} results, one for each of the following inputs. " 

    if analyser_type == 'binary':
      prompt = prompt + "Print results as one word (either positive or negative) in sequence, each seperated by a new line. Do not include any other numbers or text."

    if analyser_type == 'score':
      prompt = prompt + "Print results as one number (either 0, 1, 2, 3, 4, or 5) in sequence, each seperated by a new line. Do not include any other numbers or text."

    if analyser_type == 'opinion':
      prompt = prompt + "Print results as your expert opinion in 2-3 sentences for each input, each separated by a new line. Keep your responses concise and focused."

    if analyser_format == "text":
      prompt = prompt + "\n-----\nINPUT:\n"
      for index, ex in enumerate(inference_examples):
        example_text = f"TEXT-{index}:{ex}\n"
        prompt += example_text
      prompt = prompt + "--\nOUTPUT:"  

      return prompt

    elif analyser_format == "image":
      prompt = prompt + "\n-----\nINPUT:\n"
      test_content = [
        {
            "type": "text",
            "text": prompt
        }
      ]

      for i, ex in enumerate(inference_examples):
          img_url = f"data:image/jpeg;base64,{ex}"

          imagetag={
              "type": "text",
              "text": "IMAGE-"+str(i)+":"
          }
          image = {
              "type": "image_url",
              "image_url": {
                  "url": img_url,
                  "detail":"low"
              }
          }

          test_content.append(imagetag)
          test_content.append(image)

      prompt_end = {
        "type": "text",
        "text": "--\nOUTPUT:"
      }

      test_content.append(prompt_end)

      return test_content
    
    elif analyser_format == "textimage":
        
        test_content = [
          {
              "type": "text",
              "text": prompt + "\n-----\nINPUT:\n"
          }
        ]

        for index, ex in enumerate(inference_examples):

          example_text = {
              "type": "text",
              "text": f"TEXT-{index}:{ex['text']}\n"
          }

          test_content.append(example_text)
          img_url = f"data:image/jpeg;base64,{ex['image']}"

          imagetag={
              "type": "text",
              "text": "IMAGE-"+str(index)+":"
          }
          image = {
              "type": "image_url",
              "image_url": {
                  "url": img_url,
                  "detail":"low"
              }
          }

          test_content.append(imagetag)
          test_content.append(image)

      
        prompt_end = {
          "type": "text",
          "text": "--\nOUTPUT:"
        }

        test_content.append(prompt_end)

        return test_content
      
    return None

  except Exception as e:
    print(e)



def make_predictions(system_prompt,prompt_examples,test_set_indices,test_set,analyser_type,analyser_format):

  if analyser_format == "text":
    prompt_batch_size = 10
  else:
    prompt_batch_size = 5

  i = 0
  pred_count = 0
  batch_count = 1
  max_retry_count = 2
  retry_count = 0
  prediction_type = analyser_format

  predictions = []

  while i < len(test_set_indices):
    try:
      if retry_count == max_retry_count:
        i+= prompt_batch_size
        batch_count += 1
        retry_count = 0
      
      batch_indices = test_set_indices[i: min(i+prompt_batch_size, len(test_set))]

      if len(batch_indices) > 0:
        if len(test_set[0]['content']) > 0: 
          if prediction_type == "text":
            final_test_batch = [next((x for x in item["content"] if x['content_type'] == 'text'), None)['content_value']['text'] for i, item in enumerate(test_set) if i in batch_indices]
          elif prediction_type == "image":
            final_test_batch=[]
            for itt, item in enumerate(test_set):
              if itt in batch_indices:
                content_val = next((x for x in item["content"] if x['content_type'] == 'image'), None)["content_value"]
                base64embeddings = [e['value'] for e in content_val["embeddings"] if ("embeddings" in content_val and e['format']=="base64")]
                if len(base64embeddings)>0:
                  final_test_batch.append(base64embeddings[0])
                else:
                  print("NO EMBEDDING")
          elif prediction_type == "textimage":
            text = [next((x for x in item["content"] if x['content_type'] == 'text'), None)['content_value']['text'] for i, item in enumerate(test_set) if i in batch_indices]
            images=[]
            for itt, item in enumerate(test_set):
              if itt in batch_indices:
                content_val = next((x for x in item["content"] if x['content_type'] == 'image'), None)["content_value"]
                base64embeddings = [e['value'] for e in content_val["embeddings"] if ("embeddings" in content_val and e['format']=="base64")]
                if len(base64embeddings)>0:
                  images.append(base64embeddings[0])
                else:
                  print("NO EMBEDDING")
            final_test_batch = [{
              "image":image_data,
              "text": text[index] if index < len(text) else ""
            } for index, image_data in enumerate(images)]

        # Get batch results
        result = get_batch_predictions(i,final_test_batch,system_prompt,analyser_type,prediction_type,prompt_examples,batch_indices)

        if (result['status'] == 'success'):
          batch_results = {
            "batch_num":batch_count,
            "batch_indicies":batch_indices,
            "status":result["status"],
            "results":result["res"],
            "end_time":result["end"]
          }
        elif (result['status'] == 'filtered_success'):
          batch_results = {
            "batch_num":batch_count,
            "batch_indicies":batch_indices,
            "status":result["status"],
            "results":result["res"],
            "end_time":result["end"],
            "error":result["error"]
          }
        else:
          batch_results = {
            "batch_num":batch_count,
            "batch_indicies":batch_indices,
            "status":"fail",
            "results":[],
            "error":result["error"] if "error" in result else ""
          }                    
        
      else:
        i+= prompt_batch_size
        batch_results = None
      
      if batch_results!=None:
        predictions.append(batch_results)
        pred_count += len(batch_results['results'])
        i+= prompt_batch_size
        batch_count += 1
      else:
        if (len(batch_indices) > 0) and (batch_results['status']=="success"):
          raise Exception("Error: Batch results length zero")
        else:
          batch_results = []

    except Exception as e:
      print(e)
      error_string = "Prediction error for batch " + str(batch_count) + ". Re-running predictions for items " + str(batch_indices)
      print(error_string)
      retry_count += 1
      pass

  return predictions



def get_batch_predictions(i,test_batch, system_prompt, analyser_type, analyser_format, prompt_examples=None, test_indices=None):
    try:
      trancename = ""
      token_usage = None
      batch_start_time = round(datetime.now().timestamp() * 1000)

      user_prompt = create_user_prompt(test_batch, analyser_type, analyser_format)
      response_text = ""
      predictions = []
      batch_end_time = None
      metrics = None

      # Get results from chosen AI provider
      # Use Ollama for text tasks (default), Blip2 for image tasks
      if model_source == "openai":
        model_result = provider_openai.get_openai_gpt_response(system_prompt, user_prompt)
        if model_result['status']=="200":
          batch_end_time = model_result["end"]
          response_text = model_result["res"]
          token_usage = model_result["token"]
      else:
        # Default: Use Ollama for text tasks
        from . import provider_ollama as provider_ollama
        provider_ollama.init_ollama()
        model_result = provider_ollama.get_ollama_gpt_response(system_prompt, user_prompt)
        if model_result.get('status') == "200":
          batch_end_time = model_result.get("end")
          response_text = model_result.get("res", "")
          token_usage = model_result.get("token")
        

      if len(response_text)>0:

        predictions = re.split(r'\n+', response_text) 

        if analyser_type == 'binary': 
          predictions = [clean_response_string(p.strip().lower()) for p in predictions if ("positive" in p.lower()) or ("negative" in p.lower()) or ("content_filter" in p.lower())] #[p.strip() for p in predictions]

          predictions = [extract_binary_result(p) for p in predictions]

          for p in set(predictions):
            if not(p.lower() in ['positive', 'negative', 'content_filter']): 
              raise Exception("Results Error: Invalid response: '" + p + "'")
            
        if analyser_type == 'score':
          predictions = [extract_score_result(p) for p in predictions]
          predictions = [p for p in predictions if p!= None]

          for p in set(predictions):
            if not (p in ['0', '1', '2', '3', '4', '5','content_filter']):
              raise Exception("Results Error: Invalid response: '" + p + "'")

        if analyser_type == 'opinion':
          predictions = [p.strip() for p in predictions if p.strip() and p.strip() != 'content_filter']
          predictions = [p for p in predictions if p and len(p) > 0]

        if len(test_batch) != len(predictions):
          raise Exception("Results Error: Missing predictions: Expected " + str(len(test_batch)) + " received " + str(len(predictions)))

        return {
            "status":"success",
            "end":batch_end_time,
            "res":predictions
          }
      else:
        return {
          "status":"fail",
          "error":model_result
        }

    except Exception as e:
      print(e)



def compute_accuracy(labels,dataset,trained_example_ids,predictions,analyser_type,analyser_format,isBaseline):
  print("compute_accuracy")
  # TODO, revise this function
    



# ================================================
# HELPER FUNCTIONS
# ================================================

def extract_score_result(prediction):
  if ("content_filter" in prediction):
    result = "content_filter"
  else:
    number_results = re.findall(r'\b\d+\b', prediction)
    if (len(number_results)>0):
      result = "".join(number_results)
    else:
      result = None
  return result


def extract_binary_result(prediction):
  result = 'positive' if 'positive' in prediction.lower() else 'negative' if 'negative' in prediction.lower() else 'content_filter' 
  return result


def clean_response_string(string) :
  result = ''.join([s for s in string if s.isalnum() or s.isspace()])
  return result


def removeItemEmbeddings(item):
  image_content_obj = next((x for x in item["content"] if x['content_type'] == 'image'), None)
  image_content_obj['content_value']["embeddings"] = []
  return item

