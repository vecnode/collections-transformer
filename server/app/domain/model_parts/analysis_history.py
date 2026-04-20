class AnalysisHistory():
    def create(user_id, dataset_id, selected_items, chat_messages, analysis_summary, agent_id=None, analyser_id=None):
        """Create a new analysis history record"""
        london_tz = pytz.timezone('Europe/London')
        current_time = datetime.datetime.now(london_tz)
        
        analysis_obj = {
            "user_id": user_id,
            "dataset_id": dataset_id,
            "selected_items": selected_items,
            "selected_items_count": len(selected_items),
            "chat_messages": chat_messages,
            "analysis_summary": analysis_summary,
            "created_at": current_time,
            "status": "completed"
        }
        if agent_id:
            analysis_obj["agent_id"] = agent_id
        if analyser_id:
            analysis_obj["analyser_id"] = analyser_id
        
        analysis_id = analysis_history_collection.insert_one(analysis_obj).inserted_id
        return str(analysis_id)
    
    def get_all(user_id):
        """Get all analysis history for a user"""
        try:
            analyses = list(analysis_history_collection.find({"user_id": user_id}).sort("created_at", -1))
            
            for analysis in analyses:
                analysis["_id"] = str(analysis["_id"])
                if analysis.get("analyser_id"):
                    analysis["analyser_id"] = str(analysis["analyser_id"])
                if analysis.get("agent_id"):
                    analysis["agent_id"] = str(analysis["agent_id"])
                analysis["dataset_id"] = str(analysis["dataset_id"])
                analysis["created_at"] = analysis["created_at"].isoformat()
            
            return analyses
        except Exception as e:
            print(f"Error getting analysis history: {e}")
            return []
    
    def get(analysis_id):
        """Get a specific analysis by ID"""
        try:
            analysis = analysis_history_collection.find_one({"_id": ObjectId(analysis_id)})
            if analysis:
                analysis["_id"] = str(analysis["_id"])
                if analysis.get("analyser_id"):
                    analysis["analyser_id"] = str(analysis["analyser_id"])
                if analysis.get("agent_id"):
                    analysis["agent_id"] = str(analysis["agent_id"])
                analysis["dataset_id"] = str(analysis["dataset_id"])
                analysis["created_at"] = analysis["created_at"].isoformat()
            return analysis
        except Exception as e:
            print(f"Error getting analysis: {e}")
            return None
    
    def delete(analysis_id):
        """Delete an analysis history record"""
        try:
            analysis_history_collection.delete_one({"_id": ObjectId(analysis_id)})
            return True
        except Exception as e:
            print(f"Error deleting analysis: {e}")
            return False


