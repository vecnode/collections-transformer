@endpoints_bp.route('/backend/model_source', methods=['GET', 'POST']) 
def getModeSource():
    try: 
      return jsonify({
        "status": "200",
        "data": model
      }),200
    except Exception as e:
      print("ERROR in model source endpoint")
      print(e)
      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500


@endpoints_bp.route('/backend/dataset', methods=['GET', 'POST']) 
def getDataset(dataset_id="",includeArtworks=False, includeEmbeddings=False):
    try: 
      dataset_id = ObjectId(request.args.get('dataset_id')) if request.args.get('dataset_id') else dataset_id
      includeItems = bool(request.args.get('include_items')) if request.args.get('include_items') else bool(includeArtworks)

      dataset = models.Dataset.get(dataset_id,includeItems,False)

      return jsonify({
        "status": "200",
        "data": dataset
      }),200
    except Exception as e:
      print("ERROR in dataset endpoint")
      print(e)
      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500


@endpoints_bp.route('/backend/datasets', methods=['GET']) 
def getDatasets():
  try:
    user_id = request.args.get("user_id")
    datasets_list = models.Dataset.get_all(user_id)
    return jsonify({
      "status": "200",
      "data": datasets_list
    }),200
  except Exception as e:
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500


@endpoints_bp.route('/backend/category', methods=['GET', 'POST']) 
def getCategory(category_id):
  if request.method == 'GET':
    try: 
      category_id = ObjectId(request.args.get('category_id')) if request.args.get('category_id') else category_id
      category = models.Category.get(category_id)
      return jsonify({
        "status": "200",
        "data": category
      }),200
    except Exception as e:
      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500


@endpoints_bp.route('/backend/categories', methods=['GET']) 
def getCategories():
  try:
    user_id = request.args.get("user_id")
    categories_list = models.Category.get_all(user_id)
    return jsonify({
      "status": "200",
      "data": categories_list
    }),200
  except Exception as e:
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500



@endpoints_bp.route('/backend/category_add', methods=['POST'])
def createCategory():
    try:
      category_name = request.args.get('name')
      owner = request.args.get('user_id')
      category = {
        "name": category_name,
        "owner": owner
      } 
      category_id = models.category_collection.insert_one(category)
      return jsonify({
        "status": "200",
        "message": "Category " + category_name + " has been created with ID " + str(category_id)
      },200)
    
    except Exception as e:
      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500


@endpoints_bp.route('/backend/category_delete', methods=['POST'])
def category_delete():
  try:
    category_id = request.args.get('category_id')
    models.category_collection.delete_one({"_id": ObjectId(category_id)})
    return jsonify({
        "status": "200",
        "message": "Category " + str(category_id) + " has been deleted"
    },200)
  
  except Exception as e:
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500



@endpoints_bp.route('/backend/labelsets', methods=['GET'])
def labelsets(includeLabels=False, includeNames=True, includeCount=True):
  try:
    includeLabels = bool(request.args.get('include_labels')) if request.args.get('include_labels') else bool(includeLabels)
    includeNames = bool(request.args.get('include_names')) if request.args.get('include_names') else bool(includeNames)
    includeCount = bool(request.args.get('include_count')) if request.args.get('include_count') else bool(includeCount)
    dataset_id = ObjectId(request.args.get('dataset_id')) if request.args.get('dataset_id') else None
    label_type = request.args.get('label_type') if request.args.get('label_type') else None
    user_id = request.args.get('user_id') if request.args.get('user_id') else None
    if dataset_id != None or label_type != None:
      labelsets = models.Labelset.get_all(user_id, dataset_id, label_type, includeLabels, includeNames, includeCount)
    else:
      labelsets = models.Labelset.all(user_id,includeLabels,includeNames, includeCount)
    
    return jsonify({
      "status": "200",
      "data": labelsets
    })
  
  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500


@endpoints_bp.route('/backend/labelset', methods=['GET'])
def labelset():
  try:
    labelset_id = ObjectId(request.args.get('labelset_id'))
    includeLabels = bool(request.args.get('include_labels'))
    labelset = models.Labelset.get(None,labelset_id,includeLabels)
    # ObjectIds are already converted to strings in Labelset.get()
    return jsonify({
      "status": "200",
      "data": labelset
    })
  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500


@endpoints_bp.route('/backend/labelset_copy', methods=['GET'])
def labelset_copy():
  try:
    labelset_id = ObjectId(request.args.get('labelset_id'))
    owner_id = request.args.get('owner_id')
    new_labelset_name = request.args.get('name')
    new_labelset = models.Labelset.get(None,labelset_id)
    new_labelset_id = models.Labelset.create(owner_id, new_labelset['dataset_id'], new_labelset['label_type'], new_labelset_name)
    models.Label.copy_all(labelset_id, new_labelset_id, None)
    new_labelset_id = str(new_labelset_id)
    return jsonify({
      "status": "200",
      "data": new_labelset_id
    })
  
  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500


@endpoints_bp.route('/backend/labelset_new', methods=['GET'])
def labelset_new():
  try:
    labelset_name = request.args.get('name')
    labelset_type = request.args.get('type')
    dataset_id = ObjectId(request.args.get('dataset_id'))
    analyser_id = ObjectId(request.args.get('analyser_id')) if request.args.get('analyser_id') else None
    owner_id = request.args.get('owner_id')

    labelset_id = models.Labelset.create(owner_id,dataset_id,labelset_type,labelset_name,analyser_id)
    labelset_id = str(labelset_id)

    return jsonify({
      "status": "200",
      "data": labelset_id
    })
  
  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500


@endpoints_bp.route('/backend/labelset_update', methods=['GET'])
def labelset_update():
  try:
    labelset_id = request.args.get('labelset_id') if isinstance(request.args.get('labelset_id'),ObjectId) else ObjectId(request.args.get('labelset_id'))
    update_data = json.loads(request.args.get('data'))
    models.Labelset.update(labelset_id,update_data,False)
    return jsonify({
      "status": "200",
      "message": "Labelset " + str(labelset_id) + " updated"
    })
  
  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500


@endpoints_bp.route('/backend/labelset_delete', methods=['POST'])
def labelset_delete():
  try:
    labelset_id = request.args.get('labelset_id') if isinstance(request.args.get('labelset_id'),ObjectId) else ObjectId(request.args.get('labelset_id'))
    models.Labelset.delete(labelset_id)
    return jsonify({
      "status": "200",
      "message": "Labelset " + str(labelset_id) + " deleted"
    })
  
  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500




@endpoints_bp.route('/backend/dataset_new', methods=['POST'])
def dataset_new():
    try:
      owner_id = request.args.get('owner_id')
      dataset_name = request.form['dataset_name']
      dataset_type = request.args.get('dataset_type')
      
      if dataset_type == 'text':
        dataset = request.files['text_file']
        dataset_id = models.Dataset.create(owner_id,dataset_type,dataset_name,dataset,None,None,None)
      elif dataset_type == 'image':
        image_upload_type = request.args.get('image_upload_type')
        if image_upload_type == 'image_file': 
          dataset = request.files.getlist('image_file')
          print(len(dataset))
          dataset_id = models.Dataset.create(owner_id,dataset_type,dataset_name,None,dataset,None,image_upload_type)
        else:
          dataset = request.files['image_file'] # image links
          # TODO send error_links back to frontend and display as status box
          dataset_id, error_links = models.Dataset.create(owner_id,dataset_type,dataset_name,None,dataset,None,image_upload_type)
      elif dataset_type == "textimage":
        image_upload_type = request.args.get('image_upload_type')
        if image_upload_type == 'image_file':
          text_dataset = request.files['text_file']
          image_dataset = request.files.getlist('image_file')
          dataset_id = models.Dataset.create(owner_id,dataset_type,dataset_name,text_dataset,image_dataset,None,image_upload_type)
        else:
          text_image_dataset = request.files['text_image_file']
          dataset_id, error_links = models.Dataset.create(owner_id,dataset_type,dataset_name,None,None,text_image_dataset,image_upload_type)

      if dataset_type == 'image' and image_upload_type == 'image_link':
        return jsonify({
        "status": "200",
        "message": "Dataset has been created",
        "data": error_links
        })
      else:
        return jsonify({
          "status": "200",
          "message": "Dataset has been created"
        })
    except Exception as e:
      
      print(e)
      print(traceback.format_exc())

      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500


@endpoints_bp.route('/backend/dataset_delete', methods=['POST'])
def dataset_delete():
  try:
    dataset_id = request.args.get('dataset_id')
    models.Dataset.delete(dataset_id)
    return jsonify({
      "status": "200",
      "message": "Dataset " + str(dataset_id) + " has been deleted"
    })
  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500


@endpoints_bp.route('/backend/dataset_status', methods=['GET'])
def dataset_status():
  try:
    dataset_id = request.args.get('dataset_id')
    dataset_db_res = models.dataset_collection.find({"_id": ObjectId(dataset_id)},{"status":1, "artwork_count":1})
    dataset_res = list(dataset_db_res)
    dataset = dataset_res[0]
    return jsonify({
      "status": "200",
      "data": {"id":dataset_id, "status":dataset['status']}
    }),200
  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500


@endpoints_bp.route('/backend/dataset_update', methods=['GET'])
def dataset_update():
  try:
    dataset_id = request.args.get('dataset_id')
    data = json.loads(request.args.get("data"))
    models.Dataset.update(dataset_id,data)
    return jsonify({
      "status": "200",
      "message": "Dataset " + dataset_id + " updated"
    }),200
  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500




