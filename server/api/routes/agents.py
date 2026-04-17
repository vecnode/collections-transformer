@endpoints_bp.route('/backend/agent_new', methods=['POST'])
def createAgent():
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        task_type = data.get('task_type')
        user_id = data.get('user_id')
        
        if not all([name, description, user_id]):
            return jsonify({
                "status": "400",
                "error": "Missing required fields: name, description, user_id"
            }), 400
        
        config = data.get('config', None)
        agent_id = models.Agent.create(
            owner_id=user_id,
            name=name,
            description=description,
            task_type=task_type,
            config=config
        )
        
        if agent_id:
            return jsonify({
                "status": "200",
                "message": f"Agent '{name}' has been created successfully",
                "data": {
                    "agent_id": agent_id
                }
            }), 200
        else:
            raise Exception("Failed to create agent")
    
    except Exception as e:
        print("ERROR in createAgent")
        print(e)
        print(traceback.format_exc())
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/agent_execute', methods=['POST'])
def executeAgent():
    try:
        data = request.get_json()
        agent_id = data.get('agent_id')
        user_message = data.get('user_message', '')
        user_id = data.get('user_id')
        
        if not agent_id:
            return jsonify({
                "status": "400",
                "error": "Missing required field: agent_id"
            }), 400
        
        # Get agent from database
        agent = models.Agent.get(agent_id)
        if not agent:
            return jsonify({
                "status": "404",
                "error": "Agent not found"
            }), 404
        
        # Check ownership
        if agent.get('owner') != user_id:
            return jsonify({
                "status": "403",
                "error": "Unauthorized access to agent"
            }), 403
        
        # Get system prompt from agent
        system_prompt = agent.get('system_prompt', agent.get('description', ''))
        
        # Get config
        config = agent.get('config', {})
        max_words = config.get('max_tokens', 1000) / 1.3  # Convert tokens to words
        
        # Initialize Ollama if not already done
        try:
            provider_ollama.init_ollama()
        except:
            pass  # Already initialized
        
        # Execute with Ollama
        result = provider_ollama.get_ollama_gpt_response(
            primer_message=system_prompt,
            user_message=user_message,
            max_words=int(max_words) if max_words else None
        )
        
        if result.get('status') == '200':
            return jsonify({
                "status": "200",
                "data": {
                    "response": result.get('res', ''),
                    "token_usage": result.get('token', {}),
                    "agent_id": agent_id,
                    "agent_name": agent.get('name', '')
                }
            }), 200
        else:
            return jsonify({
                "status": "500",
                "error": result.get('error', 'Failed to execute agent')
            }), 500
    
    except Exception as e:
        print("ERROR in executeAgent")
        print(e)
        print(traceback.format_exc())
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/agent_execute_with_images', methods=['POST'])
def executeAgentWithImages():
    """Execute agent with images using Blip2 multimodal API"""
    try:
        data = request.get_json()
        agent_id = data.get('agent_id')
        dataset_id = data.get('dataset_id')
        selected_items = data.get('selected_items', [])
        user_id = data.get('user_id')
        task = data.get('task', 'Image Detection (text)')
        service_provider = data.get('service_provider', 'Ollama')
        
        print("=" * 80)
        print("AGENT EXECUTE WITH IMAGES - REQUEST RECEIVED")
        print("=" * 80)
        print(f"Agent ID: {agent_id}")
        print(f"Dataset ID: {dataset_id}")
        print(f"Selected Items: {selected_items}")
        print(f"Task: {task}")
        print(f"Service Provider: {service_provider}")
        print("=" * 80)
        
        # Validation
        if not agent_id:
            return jsonify({
                "status": "400",
                "error": "Missing required field: agent_id"
            }), 400
        
        if not dataset_id:
            return jsonify({
                "status": "400",
                "error": "Missing required field: dataset_id"
            }), 400
        
        if not selected_items or len(selected_items) == 0:
            return jsonify({
                "status": "400",
                "error": "No items selected for analysis"
            }), 400
        
        # Get agent from database
        print(f"\n[FETCHING AGENT FROM DATABASE]")
        print(f"Agent ID (string): {agent_id}")
        print(f"Agent ID type: {type(agent_id)}")
        print(f"User ID: {user_id}")
        
        try:
            agent = models.Agent.get(agent_id)
            print(f"Agent retrieved: {agent is not None}")
            
                # Use agent's task_type if available, otherwise fall back to request parameter
            if agent and agent.get('task_type'):
                task = agent.get('task_type')
                print(f"Using agent's task_type: {task}")
            
            if agent:
                print(f"Agent name: {agent.get('name', 'N/A')}")
                print(f"Agent owner: {agent.get('owner', 'N/A')}")
            else:
                print("Agent is None - not found in database")
                # Try to list all agents for debugging
                all_agents = models.Agent.get_all(user_id)
                print(f"User has {len(all_agents)} agents total")
                for ag in all_agents:
                    print(f"  - Agent ID: {ag.get('_id')}, Name: {ag.get('name')}")
        except Exception as agent_error:
            print(f"Exception while fetching agent: {agent_error}")
            print(traceback.format_exc())
            return jsonify({
                "status": "500",
                "error": f"Error fetching agent: {str(agent_error)}"
            }), 500
        
        if not agent:
            print("\n[ERROR] Agent not found in database")
            return jsonify({
                "status": "404",
                "error": f"Agent not found with ID: {agent_id}"
            }), 404
        
        # Check ownership
        if agent.get('owner') != user_id:
            return jsonify({
                "status": "403",
                "error": "Unauthorized access to agent"
            }), 403
        
        # Get system prompt from agent
        system_prompt = agent.get('system_prompt', agent.get('description', ''))
        print(f"\n[AGENT SYSTEM PROMPT]\n{system_prompt}\n")
        
        # Get config
        config = agent.get('config', {})
        max_words = config.get('max_tokens', 1000) / 1.3  # Convert tokens to words
        
        # Get dataset with artworks
        dataset = models.Dataset.get(ObjectId(dataset_id), True, False)
        if not dataset:
            return jsonify({
                "status": "404",
                "error": "Dataset not found"
            }), 404
        
        # Collect images from selected items
        images_base64 = []
        items_processed = []
        
        print(f"\n[PROCESSING {len(selected_items)} ITEM(S)]")
        for item_id_str in selected_items:
            try:
                item_id = ObjectId(item_id_str)
                # Find item in dataset artworks
                item = None
                for artwork in dataset.get('artworks', []):
                    if artwork.get('_id') == item_id_str:
                        item = artwork
                        break
                
                if not item:
                    print(f"  ⚠️  Item {item_id_str} not found in dataset")
                    continue
                
                # Extract images from item content
                item_content = item.get('content', [])
                for content_item in item_content:
                    if content_item.get('content_type') == 'image':
                        image_storage_id = content_item.get('content_value', {}).get('image_storage_id')
                        if image_storage_id:
                            try:
                                # Get image as base64
                                img_base64 = models.Item.getImage(item_id, image_storage_id)
                                # Decode from bytes to string
                                if isinstance(img_base64, bytes):
                                    img_base64_str = img_base64.decode('utf-8')
                                else:
                                    img_base64_str = img_base64
                                
                                images_base64.append(img_base64_str)
                                items_processed.append(item_id_str)
                                print(f"  ✓ Image extracted from item {item_id_str}")
                            except Exception as img_error:
                                print(f"  ✗ Error extracting image from item {item_id_str}: {img_error}")
                                continue
                
            except Exception as item_error:
                print(f"  ✗ Error processing item {item_id_str}: {item_error}")
                continue
        
        if len(images_base64) == 0:
            return jsonify({
                "status": "400",
                "error": "No images found in selected items"
            }), 400
        
        print(f"\n[IMAGES COLLECTED: {len(images_base64)}]")
        
        # Build user message based on task, including item IDs for reference
        item_ids_text = ", ".join(items_processed) if items_processed else "selected items"
        task_messages = {
            "Text Detection (T/F)": f"Analyze the text in the image(s) from items {item_ids_text} and determine if it meets the criteria. Return True or False.",
            "Text Detection (score)": f"Analyze the text in the image(s) from items {item_ids_text} and provide a score from 0-5.",
            "Text Detection (text)": f"Extract and analyze the text content in the image(s) from items {item_ids_text}.",
            "Image Detection (T/F)": f"Analyze the image(s) from items {item_ids_text} and determine if they meet the criteria. Return True or False. The image(s) are provided below.",
            "Image Detection (score)": f"Analyze the image(s) from items {item_ids_text} and provide a score from 0-5 based on the criteria. The image(s) are provided below.",
            "Image Detection (text)": f"Analyze the image(s) from items {item_ids_text} and provide a detailed text description. The image(s) are provided below."
        }
        user_message = task_messages.get(task, f"Analyze the image(s) from items {item_ids_text} according to the task: {task}. The image(s) are provided below.")
        
        print(f"\n[USER MESSAGE]\n{user_message}\n")
        print(f"[ITEM IDs IN PROMPT]\n{item_ids_text}\n")
        
        # Two-step process: Blip2 analyzes image, then Ollama processes the text
        from . import provider_blip2 as provider_blip2
        from . import provider_ollama as provider_ollama
        
        # STEP 1: Use Blip2 to analyze the image and get text description
        # Blip2 should only describe the image - it's not designed for True/False decisions
        # The agent's context will be used in step 2 with Ollama
        print("\n[STEP 1: CALLING BLIP2 MULTIMODAL API]")
        print(f"Purpose: Get detailed image description (agent context will be used in step 2)")
        print(f"Images: {len(images_base64)} image(s)")
        print("-" * 80)
        
        # Request more detailed descriptions from Blip2
        # If max_words not specified, request ~200 words (which translates to ~300 tokens)
        blip2_max_words = int(max_words) if max_words else 200
        
        blip2_result = provider_blip2.get_blip2_multimodal_response(
            primer_message="You are an expert image analyzer. Describe what you see in this image in detail, including all objects, people, scenes, colors, and any notable features.",
            user_message="Provide a detailed description of this image.",
            images=images_base64,
            max_words=blip2_max_words
        )
        
        print("\n[BLIP2 RESPONSE RECEIVED]")
        print(f"Status: {blip2_result.get('status')}")
        if blip2_result.get('status') == '200':
            blip2_response_text = blip2_result.get('res', '')
            print(f"Blip2 Response Length: {len(blip2_response_text)} characters")
            print(f"Blip2 Response: {blip2_response_text}")
            print(f"Blip2 Token Usage: {blip2_result.get('token', {})}")
        else:
            print(f"Blip2 Error: {blip2_result.get('error', 'Unknown error')}")
            return jsonify({
                "status": blip2_result.get('status', '500'),
                "error": f"Blip2 error: {blip2_result.get('error', 'Unknown error')}"
            }), 500
        
        # STEP 2: Send Blip2 response + agent context to Ollama for True/False decision
        print("\n" + "=" * 80)
        print("[STEP 2: CALLING OLLAMA WITH BLIP2 RESPONSE]")
        print("=" * 80)
        
        # Build prompt for Ollama: agent context + Blip2 description + instruction
        ollama_system_prompt = system_prompt  # Agent's system prompt/context
        ollama_user_prompt = f"""Based on the following image description, return only True or False according to the agent's criteria.

Image Description (from Blip2):
{blip2_response_text}

Agent Criteria: {system_prompt}

Return only True or False (no additional text)."""
        
        print(f"Ollama System Prompt: {ollama_system_prompt[:100]}...")
        print(f"Ollama User Prompt: {ollama_user_prompt[:200]}...")
        print("-" * 80)
        
        # Initialize Ollama if needed
        try:
            provider_ollama.init_ollama()
        except:
            pass  # Already initialized
        
        ollama_result = provider_ollama.get_ollama_gpt_response(
            primer_message=ollama_system_prompt,
            user_message=ollama_user_prompt,
            max_words=50  # Short response, just True/False
        )
        
        print("\n[OLLAMA RESPONSE RECEIVED]")
        print(f"Status: {ollama_result.get('status')}")
        if ollama_result.get('status') == '200':
            ollama_response_text = ollama_result.get('res', '').strip()
            print(f"Ollama Response: {ollama_response_text}")
            print(f"Ollama Token Usage: {ollama_result.get('token', {})}")
        else:
            print(f"Ollama Error: {ollama_result.get('error', 'Unknown error')}")
            return jsonify({
                "status": ollama_result.get('status', '500'),
                "error": f"Ollama error: {ollama_result.get('error', 'Unknown error')}"
            }), 500
        
        print("=" * 80)
        
        # Return both responses
        return jsonify({
            "status": "200",
            "result": ollama_response_text,  # Final True/False answer
            "blip2_description": blip2_response_text,  # Image description from Blip2
            "agent_name": agent.get('name', ''),
            "items_analyzed": len(items_processed),
            "token_usage": {
                "blip2": blip2_result.get('token', {}),
                "ollama": ollama_result.get('token', {})
            },
            "agent_id": agent_id
        }), 200
    
    except Exception as e:
        print("\n" + "=" * 80)
        print("ERROR in executeAgentWithImages")
        print("=" * 80)
        print(str(e))
        print(traceback.format_exc())
        print("=" * 80)
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/agents', methods=['GET'])
def getAgents():
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "Missing required parameter: user_id"
            }), 400
        
        agents = models.Agent.get_all(user_id)
        
        return jsonify({
            "status": "200",
            "data": agents
        }), 200
    
    except Exception as e:
        print("ERROR in getAgents")
        print(e)
        print(traceback.format_exc())
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/agent_delete', methods=['POST'])
def deleteAgent():
    try:
        data = request.get_json()
        agent_id = data.get('agent_id')
        
        if not agent_id:
            return jsonify({
                "status": "400",
                "error": "Missing required parameter: agent_id"
            }), 400
        
        success = models.Agent.delete(agent_id)
        
        if success:
            return jsonify({
                "status": "200",
                "message": "Agent deleted successfully"
            }), 200
        else:
            return jsonify({
                "status": "500",
                "error": "Failed to delete agent"
            }), 500
    
    except Exception as e:
        print("ERROR in deleteAgent")
        print(e)
        print(traceback.format_exc())
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


