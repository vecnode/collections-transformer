@endpoints_bp.route('/backend/analysis/save', methods=['POST'])
def save_analysis():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        analyser_id = data.get('analyser_id')
        dataset_id = data.get('dataset_id')
        selected_items = data.get('selected_items', [])
        chat_messages = data.get('chat_messages', [])
        analysis_summary = data.get('analysis_summary', {})
        
        if not all([user_id, analyser_id, dataset_id]):
            return jsonify({"status": "400", "error": "Missing required fields"})
        
        analysis_id = models.AnalysisHistory.create(
            user_id=user_id,
            analyser_id=analyser_id,
            dataset_id=dataset_id,
            selected_items=selected_items,
            chat_messages=chat_messages,
            analysis_summary=analysis_summary
        )
        
        return jsonify({"status": "200", "analysis_id": analysis_id})
    
    except Exception as e:
        print(f"Error saving analysis: {e}")
        return jsonify({"status": "500", "error": str(e)})



@endpoints_bp.route('/backend/analysis/history', methods=['GET'])
def get_analysis_history():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"status": "400", "error": "Missing user_id"})
        
        analyses = models.AnalysisHistory.get_all(user_id)
        for analysis in analyses:
            try:
                analyser = models.Analyser.get(analysis['analyser_id'], includeNames=True)
                analysis['analyser_name'] = analyser.get('name', 'Unknown') if analyser else 'Unknown'
                
                # Get dataset details
                dataset = models.Dataset.get(analysis['dataset_id'])
                analysis['dataset_name'] = dataset.get('name', 'Unknown') if dataset else 'Unknown'
                
            except Exception as e:
                print(f"Error getting details for analysis {analysis['_id']}: {e}")
                analysis['analyser_name'] = 'Unknown'
                analysis['dataset_name'] = 'Unknown'
        
        return jsonify({"status": "200", "data": analyses})
    
    except Exception as e:
        print(f"Error getting analysis history: {e}")
        return jsonify({"status": "500", "error": str(e)})




@endpoints_bp.route('/backend/analysis/delete', methods=['POST'])
def delete_analysis():
    try:
        data = request.get_json()
        analysis_id = data.get('analysis_id')
        if not analysis_id:
            return jsonify({"status": "400", "error": "Missing analysis_id"})
        success = models.AnalysisHistory.delete(analysis_id)
        if success:
            return jsonify({"status": "200", "message": "Analysis deleted successfully"})
        else:
            return jsonify({"status": "500", "error": "Failed to delete analysis"})
    
    except Exception as e:
        print(f"Error deleting analysis: {e}")
        return jsonify({"status": "500", "error": str(e)})
    


@endpoints_bp.route('/backend/item', methods=['GET'])
def getItem():
  try:
    item_id = ObjectId(request.args.get('item_id'))
    item = models.Item.get(item_id)
    formatted_item = models.Item.getFullItem(item, False)
    return jsonify({
      "status": "200",
      "data": formatted_item
    }), 200
  
  except Exception as e:
    print(f"Error in item endpoint: {e}")
    return jsonify({
      "status": "500",
      "error": str(e)
    }), 500



@endpoints_bp.route('/backend/compute_accuracy_with_samples', methods=['POST'])
def compute_accuracy_with_samples():
  try:
    data = request.get_json()
    analyser_id = ObjectId(data.get('analyser_id'))
    selected_test_samples = data.get('selected_test_samples', [])
    test_sample_labels = data.get('test_sample_labels', {})
    
    print(f"DEBUG: Received request for analyser {analyser_id}")
    print(f"DEBUG: Selected test samples: {selected_test_samples}")
    print(f"DEBUG: Test sample labels: {test_sample_labels}")
    
    if not analyser_id:
      return jsonify({"status": "400", "error": "Analyser ID is required"}), 400
    
    if not selected_test_samples:
      return jsonify({"status": "400", "error": "No test samples selected"}), 400
    
    if not test_sample_labels:
      return jsonify({"status": "400", "error": "No test sample labels provided"}), 400
    
    analyser = models.Analyser.get(analyser_id, False, True)
    if not analyser:
      return jsonify({"status": "404", "error": "Analyser not found"}), 404
    
    dataset = models.Dataset.get(analyser["dataset_id"], True)
    labelset = models.Labelset.get(None, analyser["labelset_id"], True)
    
    current_version = [v for v in analyser['versions'] if (v is not None) and (v['id'] == analyser['version'])]
    if not current_version:
      return jsonify({"status": "404", "error": "Analyser version not found"}), 404
    
    trained_example_indices = current_version[0].get('example_refs', [])
    test_items = [item for item in dataset['artworks'] if str(item['_id']) in selected_test_samples]
    
    if not test_items:
      return jsonify({"status": "400", "error": "No valid test items found"}), 400
    
    system_prompt = analyser.get('prompt', '')
    prompt_examples = current_version[0].get('examples', [])
    predictions = llm.make_predictions(
      system_prompt,
      prompt_examples,
      list(range(len(test_items))),
      test_items,
      analyser['analyser_type'],
      analyser.get('analyser_format', 'text')
    )
    
    formatted_predictions = []
    for i, item in enumerate(test_items):
      if i < len(predictions) and predictions[i].get('status') == 'success':
        pred_results = predictions[i].get('results', [])
        if i < len(pred_results):
          formatted_predictions.append({str(item['_id']): pred_results[i]})
    
    test_labels = []
    for item in test_items:
      item_id = str(item['_id'])
      if item_id in test_sample_labels:
        label_value = 1 if test_sample_labels[item_id] == 'positive' else 0
        test_labels.append({
          'item_id': item_id,
          'value': label_value,
          'rationale': ''
        })
    
    accuracy_result = llm.compute_accuracy(
      test_labels,
      test_items,
      trained_example_indices,
      formatted_predictions,
      analyser['analyser_type'],
      analyser.get('analyser_format', 'text'),
      False
    )
    
    if accuracy_result and len(accuracy_result) == 2:
      metrics, unlabelled_test_data = accuracy_result
      if isinstance(metrics, dict):
        primary_accuracy = float(metrics.get('accuracy', metrics.get('exact_accuracy', '0.0')))
      else:
        primary_accuracy = float(metrics)
      
      return jsonify({
        "status": "200",
        "message": f"Accuracy computed successfully for {len(test_items)} test samples",
        "data": {
          "accuracy": primary_accuracy,
          "metrics": metrics,
          "test_samples_processed": len(test_items),
          "predictions_made": len(formatted_predictions)
        }
      }), 200
    else:
      return jsonify({"status": "500", "error": "Accuracy computation failed"}), 500
    
  except Exception as e:
    print("Exception in compute_accuracy_with_samples:", e)
    print(traceback.format_exc())
    return jsonify({
      "status": "500",
      "error": str(e)
    }), 500



@endpoints_bp.route('/backend/test_openrouter', methods=['GET'])
def test_openrouter():
    try:
        question = "What is the capital of Budapest?"
        if not question:
            return jsonify({
                "status": "400",
                "error": "Question parameter is required"
            }), 400

        if not settings.openrouter_api_key:
            return jsonify({
                "status": "400",
                "error": "OpenRouter is not configured. Please set OPENROUTER_API_KEY in your .env file."
            }), 400

        import requests
        import json
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "HTTP-Referer": "<YOUR_SITE_URL>",
                "X-Title": "<YOUR_SITE_NAME>",
            },
            data=json.dumps({
                "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
                "messages": [
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            })
        )
        if response.status_code == 200:
            return jsonify({
                "status": "200",
                "data": response.json()['choices'][0]['message']['content']
            }), 200
        else:
            error_message = response.json().get('error', {}).get('message', 'Unknown error')
            return jsonify({
                "status": "500",
                "error": f"OpenRouter API error: {error_message}"
            }), 500

    except Exception as e:
        print("Full error:", str(e))
        print("Error type:", type(e))
        if hasattr(e, 'response'):
            print("Response status:", e.response.status_code)
            print("Response headers:", e.response.headers)
            print("Response content:", e.response.text)
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500




@endpoints_bp.route('/backend/test_openrouter_image', methods=['GET'])
def test_openrouter_image():
    try:
        image_url = request.args.get('image_url')
        if not image_url:
            return jsonify({
                "status": "400",
                "error": "Image URL parameter is required"
            }), 400
        if not settings.openrouter_api_key:
            return jsonify({
                "status": "400",
                "error": "OpenRouter is not configured. Please set OPENROUTER_API_KEY in your .env file."
            }), 400
  
        import requests
        import json

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "<YOUR_SITE_URL>",
                "X-Title": "<YOUR_SITE_NAME>",
            },
            json={
                "model": "meta-llama/llama-4-maverick:free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "What's in this image?"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ]
            }
        )

        if response.status_code == 200:
            return jsonify({
                "status": "200",
                "data": response.json()['choices'][0]['message']['content']
            }), 200
        else:
            error_message = response.json().get('error', {}).get('message', 'Unknown error')
            return jsonify({
                "status": "500",
                "error": f"OpenRouter API error: {error_message}"
            }), 500

    except Exception as e:
        print("ERROR in test_openrouter_image endpoint")
        print("Full error:", str(e))
        print("Error type:", type(e))
        if hasattr(e, 'response'):
            print("Response status:", e.response.status_code)
            print("Response headers:", e.response.headers)
            print("Response content:", e.response.text)
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


