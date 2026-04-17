@endpoints_bp.route('/backend/findpatterns_create', methods=['POST'])
def findpatterns_create():
    try:
        data = request.get_json()
        if 'test_query' in data:
            analyser_id = data.get('analyser_id')
            if analyser_id:
                analyser = models.Analyser.get(ObjectId(analyser_id), False, False)
                if analyser:
                    system_prompt = "You are an expert assistant. Provide concise, direct answers based on the given instructions."
                    analyser_type = analyser.get('analyser_type', 'binary')
                    label_instruction = ""                    
                    max_sentences = data.get('max_sentences', 3)
                    
                    if analyser_type == 'binary':
                        label_instruction = "Label type: give me an answer only True or False"
                    elif analyser_type == 'score':
                        label_instruction = "Label type: give me an answer only 0, 1, 2, 3, 4, or 5"
                    elif analyser_type == 'opinion':
                        label_instruction = f"Label type: give me an answer only your opinion in MAXIMUM {max_sentences} sentences. Keep your response concise and focused."
                                        
                    selected_items_text = ""
                    selected_images = []
                    dataset_format = "text"
                    if 'selected_items' in data and data['selected_items']:                        
                        dataset_id = data.get('dataset_id')
                        if dataset_id:
                            dataset = models.Dataset.get(ObjectId(dataset_id), True, True)                            
                            if dataset and 'artworks' in dataset:
                                selected_texts = []
                                for item_id in data['selected_items']:
                                    item = next((item for item in dataset['artworks'] if str(item['_id']) == item_id), None)
                                    if item:
                                        text_content = ""
                                        image_content = None
                                        
                                        if 'content' in item:
                                            for content in item['content']:
                                                if content.get('content_type') == 'text' and 'content_value' in content:
                                                    text_content = content['content_value'].get('text', '')
                                                elif content.get('content_type') == 'image' and 'content_value' in content:
                                                    if 'embeddings' in content['content_value']:
                                                        base64_embeddings = [e['value'] for e in content['content_value']['embeddings'] if e.get('format') == 'base64']
                                                        if base64_embeddings:
                                                            image_content = base64_embeddings[0]
                                
                                        if text_content:
                                            selected_texts.append(text_content)
                                        
                                        if image_content:
                                            selected_images.append(image_content)
                                
                                if selected_images and selected_texts:
                                    dataset_format = "textimage"
                                elif selected_images:
                                    dataset_format = "image"
                                else:
                                    dataset_format = "text"
                                
                                if dataset_format == "text":
                                    if selected_texts:
                                        selected_items_text = f"Data to analyse: {', '.join(selected_texts)}"
                                elif dataset_format == "image":
                                    selected_items_text = f"Data to analyse: {len(selected_images)} image(s)"
                                elif dataset_format == "textimage":
                                    selected_items_text = f"Data to analyse: {len(selected_texts)} text item(s) and {len(selected_images)} image(s)"
                                                    
                    task_description = analyser.get('task_description', 'You are an expert assistant.')
                    user_prompt = f"Task description: {task_description}\n{label_instruction}"
                    if selected_items_text:
                        user_prompt += f"\n{selected_items_text}"
                    
                    annotations = data.get('annotations', [])
                    if annotations and len(annotations) > 0:
                        annotation_text = "\n\nUser annotations from previous analysis:"
                        for i, annotation in enumerate(annotations[:3], 1):  # Limit to 3 annotations
                            annotation_text += f"\n{i}. {annotation.get('content', '')}"
                        user_prompt += annotation_text
                    
                    try:
                        max_words = None
                        if analyser_type == 'opinion':
                            max_words = max_sentences * 20
                        
                        # Use user's preferred text provider, Blip2 for images
                        if dataset_format == "text":
                            # Text-only inference: Use user's preferred provider
                            user_id = data.get('user_id') or session.get('user_id')
                            if user_id:
                                preferences = models.User.get_user_preferences(user_id)
                                text_provider = preferences.get('text_provider', 'ollama')
                            else:
                                text_provider = 'ollama'  # Default
                            
                            if text_provider == 'openai':
                                from .provider_openai import get_openai_gpt_response
                                llm_response = get_openai_gpt_response(system_prompt, user_prompt, max_words)
                            else:
                                # Default to Ollama
                                provider_ollama.init_ollama()
                                llm_response = provider_ollama.get_ollama_gpt_response(system_prompt, user_prompt, max_words)
                        else:
                            # Multimodal inference (images): Use Blip2
                            from . import provider_blip2 as provider_blip2
                            if dataset_format == "image":
                                llm_response = provider_blip2.get_blip2_multimodal_response(system_prompt, user_prompt, selected_images, max_words)
                            elif dataset_format == "textimage":
                                combined_prompt = user_prompt
                                if selected_texts:
                                    combined_prompt += f"\n\nText content: {', '.join(selected_texts)}"
                                llm_response = provider_blip2.get_blip2_multimodal_response(system_prompt, combined_prompt, selected_images, max_words)
                                
                    except ImportError as import_error:
                        return jsonify({
                            "status": "500",
                            "error": f"Failed to import LLM module: {str(import_error)}",
                            "system_prompt": system_prompt,
                            "user_prompt": user_prompt
                        }), 500
                    except Exception as llm_error:
                        import traceback
                        traceback.print_exc()
                        return jsonify({
                            "status": "500",
                            "error": f"LLM processing failed: {str(llm_error)}",
                            "system_prompt": system_prompt,
                            "user_prompt": user_prompt
                        }), 500
                    
                    if llm_response and llm_response.get("status") == "200":
                        result = llm_response["res"].strip()
                        if analyser_type == 'opinion' and max_sentences:
                            sentences = re.split(r'[.!?]+', result)
                            sentences = [s.strip() for s in sentences if s.strip()]
                            if len(sentences) > max_sentences:
                                truncated_sentences = sentences[:max_sentences]
                                result = '. '.join(truncated_sentences) + '.'
                        
                        token_usage = llm_response.get("token")
                        token_info = {}
                        if token_usage:
                            token_info = {
                                "prompt_tokens": getattr(token_usage, 'prompt_tokens', 0),
                                "completion_tokens": getattr(token_usage, 'completion_tokens', 0),
                                "total_tokens": getattr(token_usage, 'total_tokens', 0)
                            }

                        final_response = {
                            "status": "200",
                            "message": "Query processed successfully",
                            "result": result,
                            "system_prompt": system_prompt,
                            "user_prompt": user_prompt,
                            "response": result,
                            "analyser_used": analyser['name'],
                            "token_usage": token_info
                        }
                        
                        return jsonify(final_response), 200
                    else:
                        return jsonify({
                            "status": "500",
                            "error": f"LLM provider returned error: {llm_response}",
                            "system_prompt": system_prompt,
                            "user_prompt": user_prompt
                        }), 500
                        import traceback
                        traceback.print_exc()
                        return jsonify({
                            "status": "500",
                            "error": f"LLM processing failed: {str(llm_error)}",
                            "system_prompt": system_prompt,
                            "user_prompt": user_prompt,
                            "debug_info": {
                                "error_type": str(type(llm_error)),
                                "full_error": str(llm_error)
                            }
                        }), 500
                else:
                    return jsonify({
                        "status": "400",
                        "error": "Analyser not found"
                    }), 400
            else:
                return jsonify({
                    "status": "400",
                    "error": "Missing analyser_id for test query"
                }), 400
        
        user_id = data.get('user_id')
        selected_items = data.get('selected_items', [])
        analyser_id = data.get('analyser_id')
        dataset_id = data.get('dataset_id')
        
        if not analyser_id or not dataset_id:
            return jsonify({
                "status": "400",
                "error": "Missing analyser_id or dataset_id"
            }), 400
        
        analyser = models.Analyser.get(ObjectId(analyser_id), False, False)
        dataset = models.Dataset.get(ObjectId(dataset_id), True, True)
        
        if not analyser or not dataset:
            return jsonify({
                "status": "400",
                "error": "Analyser or dataset not found"
            }), 400
        
        items_for_analysis = []
        if selected_items:
            for item_id in selected_items:
                item = next((item for item in dataset['artworks'] if str(item['_id']) == item_id), None)
                if item:
                    items_for_analysis.append(item)
        
        if not items_for_analysis:
            return jsonify({
                "status": "400",
                "error": "No valid items found for analysis"
            }), 400
        
        prompt, prompt_examples, example_ids = models.Analyser.createLLMprompt(
            analyser['analyser_type'],
            analyser['analyser_format'],
            analyser['task_description'],
            analyser['labelling_guide'],
            ObjectId(dataset_id),
            analyser.get('labelset_id'),
            include_examples=False
        )
        
        from .llm_modelling import use_model
        
        try:
            item_indices = []
            for item in items_for_analysis:
                item_index = next((index for index, x in enumerate(dataset['artworks']) if x['_id'] == item['_id']), None)
                if item_index is not None:
                    item_indices.append(item_index)
            
            prediction_results = use_model(prompt, prompt_examples, item_indices, items_for_analysis, analyser)
            
            return jsonify({
                "status": "200",
                "message": "Analysis completed successfully",
                "prompt": prompt,
                "items_count": len(items_for_analysis),
                "analyser_name": analyser['name'],
                "dataset_name": dataset['name'],
                "result": f"Analysis completed for {len(items_for_analysis)} items",
                "predictions": prediction_results
            }), 200
            
        except Exception as llm_error:
            print(f"LLM Analysis Error: {llm_error}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "status": "500",
                "error": f"LLM analysis failed: {str(llm_error)}",
                "prompt": prompt
            }), 500
        
    except Exception as e:
        print("Error in findpatterns_create:", e)
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500




@endpoints_bp.route('/backend/analyser_new_with_prompt', methods=['POST'])
def createAnalyserWithPrompt():
    try:
        data = request.get_json()        
        name = data.get('name')
        task_description = data.get('task_description')
        labelling_guide = data.get('labelling_guide', '')
        analyser_type = data.get('analyser_type')
        dataset_id = data.get('dataset_id')
        user_id = data.get('user_id')
        
        example_ids = data.get('example_ids', [])
        auto_select_examples = data.get('auto_select_examples', False)
        num_examples = data.get('num_examples', 5)

        if not all([name, task_description, analyser_type, user_id]):
            return jsonify({
                "status": "400",
                "error": "Missing required fields: name, task_description, analyser_type, user_id"
            }), 400

        if analyser_type == 'opinion':
            analyser_type = 'opinion'
        elif analyser_type == 'boolean':
            analyser_type = 'binary'
        elif analyser_type == 'score':
            analyser_type = 'score'

        if not dataset_id:
            return jsonify({
                "status": "400",
                "error": "Dataset selection is required"
            }), 400
            
        dataset_obj_id = ObjectId(dataset_id)
        analyser_format = "text"
        
        dataset = models.Dataset.get(dataset_obj_id)
        if dataset and dataset.get('type'):
            analyser_format = dataset['type']
        
        labelset_name = f"Labelset for {name}"
        labelset_id = models.Labelset.create(user_id, dataset_obj_id, analyser_type, labelset_name)

        item_labels = data.get('item_labels', {})
        labeled_item_ids = []
        if item_labels and isinstance(item_labels, dict):
            print(f"Processing {len(item_labels)} item labels")
            
            dataset = models.Dataset.get(dataset_obj_id, True, False)
            
            for item_id, label_value in item_labels.items():
                try:
                    item_obj_id = ObjectId(item_id)
                    labeled_item_ids.append(item_id)
                    item = None
                    content_type = 'text'
                    if dataset and 'artworks' in dataset:
                        item = next((artwork for artwork in dataset['artworks'] if str(artwork['_id']) == item_id), None)
                        if item and 'content' in item:
                            has_image = any(c.get('content_type') == 'image' for c in item['content'])
                            has_text = any(c.get('content_type') == 'text' for c in item['content'])
                            if has_image and has_text:
                                content_type = 'textimage'
                            elif has_image:
                                content_type = 'image'
                            elif has_text:
                                content_type = 'text'
                    
                    if analyser_type == 'binary':
                        label_subtype = 'positive' if label_value == 'positive' else 'negative'
                        models.BinaryLabel.create(
                            labelset_id=labelset_id,
                            item_id=item_obj_id,
                            content_type=content_type,
                            content_ref=item_obj_id,
                            label_subtype=label_subtype
                        )
                    elif analyser_type == 'score':
                        label_subtype = 'positive' if label_value == 'positive' else 'negative'
                        models.BinaryLabel.create(
                            labelset_id=labelset_id,
                            item_id=item_obj_id,
                            content_type=content_type,
                            content_ref=item_obj_id,
                            label_subtype=label_subtype
                        )
                    elif analyser_type == 'opinion':
                        label_subtype = 'positive' if label_value == 'positive' else 'negative'
                        models.BinaryLabel.create(
                            labelset_id=labelset_id,
                            item_id=item_obj_id,
                            content_type=content_type,
                            content_ref=item_obj_id,
                            label_subtype=label_subtype
                        )
                    print(f"Created {analyser_type} label for item {item_id} ({content_type}): {label_value}")
                except Exception as e:
                    print(f"Error creating label for item {item_id}: {e}")

        include_examples = len(example_ids) > 0 or auto_select_examples
        
        prompt, prompt_examples, chosen_example_ids = models.Analyser.createLLMprompt(
            analyser_type=analyser_type,
            analyser_format=analyser_format,
            task_description=task_description,
            labelling_guide=labelling_guide,
            dataset_id=dataset_obj_id,
            labelset_id=labelset_id,
            include_examples=include_examples,
            auto_select_examples=str(auto_select_examples).lower() if auto_select_examples else None,
            example_ids=example_ids if example_ids else None,
            num_examples=num_examples if auto_select_examples else None,
            examples_start_index=0,
            examples_end_index=None
        )

        final_example_refs = labeled_item_ids if labeled_item_ids else chosen_example_ids
        print(f"Final example_refs: {final_example_refs} (labeled: {labeled_item_ids}, chosen: {chosen_example_ids})")

        analyser_id = models.Analyser.create(
            owner_id=user_id,
            analyser_type=analyser_type,
            name=name,
            task_description=task_description,
            labelling_guide=labelling_guide,
            dataset_id=dataset_obj_id,
            labelset_id=labelset_id,
            category_id=None,
            auto_select_examples=str(auto_select_examples).lower() if auto_select_examples else None,
            chosen_example_ids=final_example_refs,
            num_examples=num_examples if auto_select_examples else 0,
            example_start_index=0,
            example_end_index=None
        )

        if analyser_id:
            return jsonify({
                "status": "200",
                "message": f"AI '{name}' has been created successfully",
                "data": {
                    "analyser_id": analyser_id,
                    "prompt": prompt,
                    "example_count": len(prompt_examples),
                    "chosen_example_ids": chosen_example_ids,
                    "auto_select_examples": auto_select_examples,
                    "num_examples": num_examples if auto_select_examples else len(example_ids)
                }
            }), 200
        else:
            raise Exception("Failed to create analyser")

    except Exception as e:
        print("ERROR in createAnalyserWithPrompt")
        print(e)
        print(traceback.format_exc())
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


# Agent endpoints
