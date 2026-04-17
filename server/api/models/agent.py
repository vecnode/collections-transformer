class Agent():

    def create(owner_id, name, description, task_type=None, config=None):
        """Create a new agent"""
        try:
            agent_args = {
                "name": name,
                "description": description,
                "system_prompt": description,  # Use description as system prompt
                "task_type": task_type or "Text Detection (T/F)",  # Default task type
                "owner": owner_id,
                "created_at": datetime.datetime.now(),
                "config": config or {
                    "temperature": 0.8,
                    "max_tokens": 1000,
                    "model": os.environ.get('OLLAMA_MODEL_OPTION', 'gemma3:27b')
                },
                "functions": []
            }
            
            agent_res = agent_collection.insert_one(agent_args).inserted_id
            agent_id = str(agent_res)
            
            return agent_id
        except Exception as e:
            print(f"Error creating agent: {e}")
            print(traceback.format_exc())
            return None

    def get(agent_id):
        """Get an agent by ID"""
        try:
            print(f"[Agent.get] Input agent_id: {agent_id}, type: {type(agent_id)}")
            agent_id_obj = agent_id if isinstance(agent_id, ObjectId) else ObjectId(agent_id)
            print(f"[Agent.get] Converted to ObjectId: {agent_id_obj}")
            agent = agent_collection.find_one({"_id": agent_id_obj})
            print(f"[Agent.get] Query result: {agent is not None}")
            if agent:
                agent["_id"] = str(agent["_id"])
                print(f"[Agent.get] Agent found: {agent.get('name', 'N/A')}")
            else:
                print(f"[Agent.get] No agent found with ID: {agent_id_obj}")
            return agent
        except Exception as e:
            print(f"Error getting agent: {e}")
            print(traceback.format_exc())
            return None

    def get_all(user_id):
        """Get all agents for a user"""
        try:
            agents = list(agent_collection.find({"owner": user_id}))
            for agent in agents:
                agent["_id"] = str(agent["_id"])
                # Convert created_at to ISO format string if it exists
                if "created_at" in agent and agent["created_at"]:
                    if isinstance(agent["created_at"], datetime.datetime):
                        agent["created_at"] = agent["created_at"].isoformat()
            return agents
        except Exception as e:
            print(f"Error getting agents: {e}")
            print(traceback.format_exc())
            return []

    def update(agent_id, update_data):
        """Update an agent"""
        try:
            agent_id = agent_id if isinstance(agent_id, ObjectId) else ObjectId(agent_id)
            result = agent_collection.update_one(
                {"_id": agent_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating agent: {e}")
            return False

    def delete(agent_id):
        """Delete an agent"""
        try:
            agent_id = agent_id if isinstance(agent_id, ObjectId) else ObjectId(agent_id)
            agent_collection.delete_one({"_id": agent_id})
            return True
        except Exception as e:
            print(f"Error deleting agent: {e}")
            return False




