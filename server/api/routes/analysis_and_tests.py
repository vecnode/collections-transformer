@endpoints_bp.route('/backend/analysis/save', methods=['POST'])
def save_analysis():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        agent_id = data.get('agent_id')
        dataset_id = data.get('dataset_id')
        selected_items = data.get('selected_items', [])
        chat_messages = data.get('chat_messages', [])
        analysis_summary = data.get('analysis_summary', {})

        if not all([user_id, dataset_id]):
            return jsonify({"status": "400", "error": "Missing required fields"})

        analysis_id = models.AnalysisHistory.create(
            user_id=user_id,
            dataset_id=dataset_id,
            selected_items=selected_items,
            chat_messages=chat_messages,
            analysis_summary=analysis_summary,
            agent_id=agent_id,
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
                analysis['agent_name'] = 'Unknown'
                if analysis.get('agent_id'):
                    agent = models.Agent.get(analysis['agent_id'])
                    analysis['agent_name'] = agent.get('name', 'Unknown') if agent else 'Unknown'
                elif analysis.get('analyser_name'):
                    analysis['agent_name'] = analysis.get('analyser_name')

                dataset = models.Dataset.get(analysis['dataset_id'])
                analysis['dataset_name'] = dataset.get('name', 'Unknown') if dataset else 'Unknown'

            except Exception as e:
                print(f"Error getting details for analysis {analysis['_id']}: {e}")
                analysis['agent_name'] = 'Unknown'
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


