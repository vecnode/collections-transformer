@endpoints_bp.route('/backend/ollama/models', methods=['GET'])
def getOllamaModels():
    try:
        result = provider_ollama.list_ollama_models()
        
        if result.get('status') == '200':
            return jsonify({
                "status": "200",
                "data": {
                    "models": result.get('models', [])
                }
            }), 200
        else:
            return jsonify({
                "status": result.get('status', '400'),
                "error": result.get('error', 'Failed to fetch Ollama models'),
                "data": {
                    "models": []
                }
            }), 200  # Return 200 even on error so frontend can handle empty list
    
    except Exception as e:
        print("ERROR in getOllamaModels")
        print(e)
        print(traceback.format_exc())
        return jsonify({
            "status": "500",
            "error": str(e),
            "data": {
                "models": []
            }
        }), 200  # Return 200 even on error so frontend can handle empty list


@endpoints_bp.route('/backend/db/inspect', methods=['GET'])
def inspectDatabase():
    """Get database structure: collections, counts, and sample documents"""
    try:
        from api import db
        
        # Get all collection names
        collection_names = db.list_collection_names()
        
        collections_data = []
        for coll_name in collection_names:
            collection = db[coll_name]
            count = collection.count_documents({})
            
            # Get a sample document (first one)
            sample_doc = collection.find_one({})
            
            # Extract field names from sample if available
            fields = []
            if sample_doc:
                fields = list(sample_doc.keys())
            
            collections_data.append({
                "name": coll_name,
                "count": count,
                "fields": fields,
                "has_sample": sample_doc is not None
            })
        
        return jsonify({
            "status": "200",
            "data": {
                "database_name": db.name,
                "collections": collections_data
            }
        }), 200
    
    except Exception as e:
        print("ERROR in inspectDatabase")
        print(e)
        print(traceback.format_exc())
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/db/collection/<collection_name>', methods=['GET'])
def getCollectionDocuments(collection_name):
    """Get documents from a specific collection (with pagination)"""
    try:
        from api import db
        from bson import json_util
        
        limit = int(request.args.get('limit', 50))
        skip = int(request.args.get('skip', 0))
        
        collection = db[collection_name]
        documents = list(collection.find({}).skip(skip).limit(limit))
        
        # Convert ObjectId and other BSON types to JSON-serializable format
        documents_json = json.loads(json_util.dumps(documents))
        
        total_count = collection.count_documents({})
        
        return jsonify({
            "status": "200",
            "data": {
                "collection_name": collection_name,
                "documents": documents_json,
                "total_count": total_count,
                "returned_count": len(documents_json),
                "has_more": (skip + len(documents_json)) < total_count
            }
        }), 200
    
    except Exception as e:
        print("ERROR in getCollectionDocuments")
        print(e)
        print(traceback.format_exc())
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


# Authentication endpoints
