@endpoints_bp.route('/backend/analyser', methods=['GET'])
def getAnalyser():
  try: 
    include_names = bool(request.args.get('include_names')) if request.args.get('include_names') else True
    include_versions = bool(request.args.get('include_versions')) if request.args.get('include_versions') else False
    if request.args.get('analyser_id') and request.args.get('analyser_id') != None:
      analyser_id = ObjectId(request.args.get('analyser_id'))
      analyser = models.Analyser.get(analyser_id,include_names,include_versions)

    return jsonify({
      "status": "200",
      "data": analyser
    }),200

  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500



@endpoints_bp.route('/backend/analyser_new', methods=['GET'])
def createAnalyser():
    try:
      name = request.args.get('name')
      dataset_id = ObjectId(request.args.get('dataset_id')) if request.args.get('dataset_id') != "" else None
      category_id = ObjectId(request.args.get('category_id')) if request.args.get('category_id') != "" else None
      user_id = request.args.get('user_id')
      task_description = request.args.get('task_description')
      analyser_type = request.args.get('analyser_type')
      labelling_guide = request.args.get('labelling_guide')
      labelset_id = ObjectId(request.args.get('labelset_id')) if request.args.get('labelset_id') != "" else None
      example_ids = request.args.get('example_ids') if request.args.get('example_ids') else None

      if example_ids:
        example_ids = json.loads(example_ids)
      else:
        example_ids = []

      if (labelset_id != None):
        labelset_data={}
        if (labelling_guide != ""): 
          labelset_data["labelling_guide"] = labelling_guide
        models.Labelset.update(labelset_id, labelset_data,False)

      analyser_id = models.Analyser.create(
        owner_id=user_id,
        analyser_type=analyser_type,
        name=name,
        task_description=task_description,
        labelling_guide=labelling_guide,
        dataset_id=dataset_id,
        labelset_id=labelset_id,
        category_id=category_id,
        auto_select_examples=None, 
        chosen_example_ids=[],
        num_examples=0,
        example_start_index=0,
        example_end_index=None
      )

      if analyser_id != None:
        return jsonify({
          "status": "200",
          "message": "Analyser " + analyser_id + " has been created",
          "data": {
            "analyser_id":analyser_id
          }
        })
      else: 
        raise

    except Exception as e:
      print("ERROR in createAnalyser")
      print(e)
      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500


@endpoints_bp.route('/backend/analyser_update', methods=['GET'])
def analyser_update():
    try:
      analyser_id = request.args.get('analyser_id')
      data = json.loads(request.args.get('update_data'))
      config = json.loads(request.args.get('analyser_config')) if request.args.get('analyser_config') else None
      newVersion = bool(request.args.get('new_version')=="true") if request.args.get('new_version') else False
      models.Analyser.update(
        analyser_id, data, config, newVersion
      )

      if analyser_id != None:
        return jsonify({
          "status": "200",
          "message": "Analyser " + analyser_id + " has been updated",
        })
      else: 
        raise Exception("Error in analyser_update")

    except Exception as e:
      print(e)
      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500


@endpoints_bp.route('/backend/analyser_change_version', methods=['GET'])
def analyser_update_version():
    try:
      analyser_id = request.args.get('analyser_id')
      version = request.args.get('version')
      if analyser_id != None and version != None:
        models.Analyser.update_version(analyser_id,version)
        return jsonify({
          "status": "200",
          "message": "Version " + version + " of analyser " + analyser_id + " loaded",
        })
      else: 
        raise Exception("Error in analyser_update_version")

    except Exception as e:
      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500


@endpoints_bp.route('/backend/analyser_change_version_details', methods=['GET'])
def analyser_update_version_details():
    try:
      analyser_id = request.args.get('analyser_id')
      version = request.args.get('version')
      data = json.loads(request.args.get('data')) if request.args.get('data') else None
      models.Analyser.update_version_details(analyser_id,version,data)
      if analyser_id != None:
        return jsonify({
          "status": "200",
          "message": "Version " + version + " of analyser " + analyser_id + " updated",
        })
      else: 
        raise Exception("Error in analyser_update_version_status")

    except Exception as e:
      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500


@endpoints_bp.route('/backend/analyser_create', methods=['GET'])
def analyser_create():
    try:
      name = request.args.get('name')
      dataset_id = request.args.get('dataset_id')
      category_id = request.args.get('category_id')
      user_id = request.args.get('user_id')
      analyser_id = models.Analyser.create(user_id,name,dataset_id,category_id)
      return jsonify({
        "status": "200",
        "message": "Analyser " + analyser_id + " has been created",
        "data": {
          "analyser_id":analyser_id
        }
      })
    except Exception as e:
      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500




@endpoints_bp.route('/backend/llm_predictions', methods=['GET'])
def llm_predictions(analyser_id=None,num_predictions=0,start=None,end=None):
  analyser_id = ObjectId(request.args.get('analyser_id')) if request.args.get('analyser_id') else ObjectId(analyser_id)
  auto_select_sample = request.args.get("auto_select_sample")
  sample_ids = request.args.get("sample_ids").split(",")
  num_predictions = int(request.args.get("num_predictions")) if request.args.get("num_predictions") else len(sample_ids)
  start_index = int(request.args.get("start")) if request.args.get("start") else start
  end_index = int(request.args.get("end")) if request.args.get("end") else end
  dataset_id = request.args.get("dataset_id") if request.args.get("dataset_id") and request.args.get("dataset_id") != 'null' else None

  try:
    predictions_res = models.Analyser.use(analyser_id,sample_ids,num_predictions,auto_select_sample,dataset_id,start_index,end_index)
    if predictions_res is not None:
      if "Runtime error" in predictions_res:
        print("Runtime exception")
        return jsonify({
          "status":"500",
          "error":"Runtime error: Your device is out of memory."
        }),500
      else:
        return jsonify({
          "status": "200",
          "message": "Predictions received for text",
          "data": {
            **predictions_res,
            "sample_ids":sample_ids
          }
        }), 200
    else:
      print("Predictions Error: Predictions not formatted correctly and/or missing values")
      return jsonify({
        "status":"500",
        "error":"Prediction Error: Please contact the technical team."
      }),500
  
  except Exception as e:
    print("exception in LLM predictions")
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500


@endpoints_bp.route('/backend/llm_accuracy', methods=['GET'])
def llm_accuracy(analyser_id=None):
# Deprecated
  analyser_id = ObjectId(request.args.get('analyser_id')) if request.args.get('analyser_id') else ObjectId(analyser_id)
  try:
    analyser = models.Analyser.get(analyser_id,False,False)
    accuracy_result = models.Analyser.getAccuracy(analyser_id)    
    if accuracy_result and len(accuracy_result) == 2:
      metrics, unlabelled_test_data = accuracy_result
      if isinstance(metrics, dict):
        primary_accuracy = float(metrics.get('accuracy', metrics.get('exact_accuracy', '0.0')))
        response_data = {
          "accuracy": primary_accuracy,
          "metrics": metrics,
          "unlabelled_test_data": unlabelled_test_data
        }
      else:
        primary_accuracy = float(metrics)
        response_data = {
          "accuracy": primary_accuracy,
          "unlabelled_test_data": unlabelled_test_data
        }
    else:
      raise Exception("Invalid accuracy result returned")
    models.Analyser.update(analyser_id,{"accuracy":primary_accuracy},None,False)
    return jsonify({
      "status": "200",
      "message": "Accuracy recieved for version " + str(analyser['version']) + " of analyser " + str(analyser_id),
      "data": response_data
    }), 200
  
  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500





@endpoints_bp.route('/backend/update_example', methods=['GET', 'POST'])
def update_example():
    try:
      obj_id = request.args.get('id')
      item_id_string = obj_id.split('artwork-')[1].split('-')[0]
      analyser_id = ObjectId(request.args.get('analyser_id'))
      is_checked = json.loads(request.args.get('checked'))
      analyser = models.Analyser.get(analyser_id,False,False)
      example_refs = analyser['example_refs']

      if (item_id_string in example_refs) and not is_checked: 
        example_refs.remove(item_id_string) 
      elif (item_id_string not in example_refs) and is_checked:
        example_refs.append(item_id_string) 
      else:
        raise Exception("Invalid status for example update " + obj_id)

      models.Analyser.update(
        analyser_id,
        {
          "example_refs":example_refs
        },
        None,
        False
      )

      return jsonify({
        "status": "200",
        "message": "Example " + str(obj_id) + " has been added" if is_checked else "Example " + str(obj_id) + " has been removed"
      })
    
    except Exception as e:
      print(e)
      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500


@endpoints_bp.route('/backend/update_sample', methods=['GET', 'POST'])
def update_sample():
    try:
      obj_id = request.args.get('id')
      item_id_string = obj_id.split('artwork-')[1].split('-')[0]
      analyser_id = ObjectId(request.args.get('analyser_id'))
      is_checked = json.loads(request.args.get('checked'))
      analyser = models.Analyser.get(analyser_id,False,False)
      sample_refs = analyser['sample_ids']
      if (item_id_string in sample_refs) and not is_checked: 
        sample_refs.remove(item_id_string) 
      elif (item_id_string not in sample_refs) and is_checked:
        sample_refs.append(item_id_string) 
      else:
        raise Exception("Invalid status for sample update " + obj_id)

      models.Analyser.update(
        analyser_id,
        {
          "sample_ids":sample_refs
        },
        None,
        False
      )
      return jsonify({
        "status": "200",
        "message": str(obj_id) + " has been added to sample" if is_checked else str(obj_id) + " has been removed from sample"
      })
    
    except Exception as e:
      print(e)
      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500



@endpoints_bp.route('/backend/update_label', methods=['GET', 'POST'])
def update_label():
    try:
      obj_id = request.args.get('id')
      item_id = ObjectId(obj_id.split('artwork-')[1].split('-')[0])
      labelset_id = ObjectId(request.args.get('labelset_id'))
      labelset = models.Labelset.get(None,labelset_id)
      label_type = labelset["label_type"]
      options = {}
      action_string = ""
      is_checked = json.loads(request.args.get('checked')) if request.args.get('checked') else None # This is the new state after clicking, not the previous state
      if is_checked != None:
        positive_tag = True if obj_id.startswith('positive') else False # True if clicked on positive label, false if clicked on Negative
        options["label_subtype"] = "positive" if positive_tag else "negative"
        options["ticked"] = is_checked
        action_string = "Value changed to " + str(is_checked)

      score = request.args.get('score') if request.args.get('score') else None
      if score != None:
        options["score"] = score
        action_string = "Value changed to " + str(score)

      rationale = request.args.get('rationale') if request.args.get('rationale') else None
      if rationale != None:
        options["rationale"] = rationale if rationale != "<Empty>" else ""
        action_string = "Rationale changed to " + rationale

      highlight = request.args.get('highlight') if request.args.get('highlight') else None
      if highlight != None:
        options["highlight"] = json.loads(highlight)
        action_string = "Highlight changed"

      exclude = request.args.get('exclude') if request.args.get('exclude') else None
      if exclude != None:
        print(exclude)
        options["exclude"] = exclude
        action_string = "Exclude changed"

      models.Label.update(
        label_type,labelset_id,item_id,item_id,"text",options
      )

      return jsonify({
        "status": "200",
        "message": "Label " + str(obj_id) + " has been updated: " + action_string
      })
    
    except Exception as e:
      print(e)
      return jsonify({
        "status":"500",
        "error":str(e) 
      }),500



@endpoints_bp.route('/backend/highlight_text', methods=['GET', 'POST'])
def highlight_text():
  try:
    item_id = request.args.get('item_id')
    subcontent_value = request.args.get('subcontent_value')
    models.Item.update_text_subcontent(item_id, subcontent_value)
    return jsonify({
          "status": "200",
          "message": "Highlighted text has been added to " + str(item_id)
        })
    
  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500
  



@endpoints_bp.route('/backend/item_image')
def get_item_image():
  item_id = ObjectId(request.args.get('item_id'))
  image_storage_id = ObjectId(request.args.get('image_storage_id'))
  img = models.Item.getImage(item_id,image_storage_id)
  decoded_img = img.decode()
  return jsonify({
      "status":"200",
      "data":decoded_img
  })







