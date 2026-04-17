import os
import re

from flask import request
from flask import jsonify
from flask import session
from bson.objectid import ObjectId
from bson import json_util
import json
from sklearn.metrics import f1_score
import api.models as models
import api.llm_modelling as llm
from app import model
from flask import Blueprint
import traceback
from . import provider_ollama


endpoints_bp = Blueprint('endpoints', __name__)

def parse_json(data):
    return json.loads(json_util.dumps(data))


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
def getDataset(analyser_id=None,dataset_id="",includeArtworks=False, includeEmbeddings=False):
    try: 
      dataset_id = ObjectId(request.args.get('dataset_id')) if request.args.get('dataset_id') else dataset_id
      analyser_id = ObjectId(request.args.get('analyser_id')) if request.args.get('analyser_id') else analyser_id
      includeItems = bool(request.args.get('include_items')) if request.args.get('include_items') else bool(includeArtworks)

      if analyser_id!=None:
        analyser = models.Analyser.get(analyser_id, False,False)
        dataset_id = analyser["dataset_id"]

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


@endpoints_bp.route('/backend/analysers', methods=['GET']) 
def getAnalysers():
  try:
    user_id = request.args.get('user_id')
    includeNames = bool(request.args.get('include_names'))
    includeVersions = bool(request.args.get('include_versions'))
    analyser_list = models.Analyser.all(user_id,includeNames,includeVersions)

    return jsonify({
      "status": "200",
      "data": analyser_list
    }),200

  except Exception as e:
    print("ERROR in classifier endpoint")
    print(f"Error details: {str(e)}")
    print(traceback.format_exc())
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


@endpoints_bp.route('/backend/classifier', methods=['GET', 'POST'])
def classifier():
  try: 
    includeNames = bool(request.args.get('include_names')) if request.args.get('include_names') else True
    if request.args.get('analyser_id') and request.args.get('analyser_id') != None:
      analyser_id = ObjectId(request.args.get('analyser_id'))
      classifier = models.Analyser.get(analyser_id,includeNames,False)

    return jsonify({
      "status": "200",
      "data": classifier
    }),200

  except Exception as e:
    print(e)
    return jsonify({
      "status":"500",
      "error":str(e) 
    }),500


@endpoints_bp.route('/backend/classifier_delete', methods=['POST'])
def classifier_delete():
  try:
    analyser_id = request.args.get('analyser_id')
    models.Analyser.delete(analyser_id)
    return jsonify({
        "status": "200",
        "message": "Analyser " + str(analyser_id) + " has been deleted"
    })
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





@endpoints_bp.route('/backend/test_openai', methods=['GET'])
def test_openai():
    try:
        question = request.args.get('question')
        if not question:
            return jsonify({
                "status": "400",
                "error": "Question parameter is required"
            }), 400
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question}
            ]
        )
        return jsonify({
            "status": "200",
            "data": response.choices[0].message.content
        }), 200
    except Exception as e:
        print("ERROR in test_openai endpoint")
        print(e)
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500







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
@endpoints_bp.route('/backend/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({
                "status": "400",
                "error": "Username, email, and password are required"
            }), 400
        
        if len(password) < 6:
            return jsonify({
                "status": "400",
                "error": "Password must be at least 6 characters"
            }), 400
        
        user_id, error = models.User.create_local_user(username, email, password)
        if error:
            return jsonify({
                "status": "400",
                "error": error
            }), 400
        
        # Set session
        session['user_id'] = user_id
        session['username'] = username
        session['email'] = email
        session.permanent = True
        
        # Record connection
        models.User.record_connection(user_id, 'register', True)
        
        return jsonify({
            "status": "200",
            "data": {
                "user_id": user_id,
                "username": username,
                "email": email
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        data = request.get_json()
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username_or_email or not password:
            return jsonify({
                "status": "400",
                "error": "Username/email and password are required"
            }), 400
        
        user_id, username, email = models.User.authenticate_local_user(username_or_email, password)
        if not user_id:
            return jsonify({
                "status": "401",
                "error": "Invalid username/email or password"
            }), 401
        
        # Set session
        session['user_id'] = user_id
        session['username'] = username
        session['email'] = email
        session.permanent = True
        
        # Record connection
        models.User.record_connection(user_id, 'login', True)
        
        return jsonify({
            "status": "200",
            "data": {
                "user_id": user_id,
                "username": username,
                "email": email
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/auth/logout', methods=['POST'])
def logout():
    try:
        user_id = session.get('user_id')
        if user_id:
            models.User.record_connection(user_id, 'logout', False)
        session.clear()
        return jsonify({
            "status": "200",
            "message": "Logged out successfully"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/auth/verify', methods=['GET'])
def verify_session():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                "status": "401",
                "authenticated": False,
                "error": "Not authenticated"
            }), 401
        
        user = models.User.get_user_by_id(user_id)
        if not user:
            session.clear()
            return jsonify({
                "status": "401",
                "authenticated": False,
                "error": "User not found"
            }), 401
        
        return jsonify({
            "status": "200",
            "authenticated": True,
            "data": {
                "user_id": user.get("user_id"),
                "username": user.get("username"),
                "email": user.get("email"),
                "role": user.get("role", ""),
                "affiliation": user.get("affiliation", "")
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/user/record_connection', methods=['POST'])
def record_user_connection():
    try:
        user_id = request.args.get('user_id')
        event_type = request.args.get('event_type', 'login')
        if not user_id and request.is_json:
            data = request.get_json()
            user_id = data.get('user_id')
            event_type = data.get('event_type', 'login')
        
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "user_id is required"
            }), 400
        
        should_update_connection = event_type in ['login', 'page_load', 'page_visible']
        models.User.record_connection(user_id, event_type, should_update_connection)
        return jsonify({
            "status": "200",
            "message": f"Connection recorded successfully for event: {event_type}"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500



@endpoints_bp.route('/backend/user/last_connection', methods=['GET'])
def get_last_connection():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "user_id is required"
            }), 400        
        user_data = models.user_collection.find_one({"user_id": user_id})
        if user_data:
            last_connection = user_data.get("previous_connection") or user_data.get("last_connection")
            return jsonify({
                "status": "200",
                "data": {
                    "first_connection": user_data.get("first_connection").isoformat() if user_data.get("first_connection") else None,
                    "last_connection": last_connection.isoformat() if last_connection else None,
                    "last_event_type": user_data.get("last_event_type"),
                    "last_event_time": user_data.get("last_event_time").isoformat() if user_data.get("last_event_time") else None
                }
            }), 200
        else:
            return jsonify({
                "status": "200",
                "data": {
                    "first_connection": None,
                    "last_connection": None,
                    "last_event_type": None,
                    "last_event_time": None
                }
            }), 200
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500




@endpoints_bp.route('/backend/user/profile', methods=['GET'])
def get_user_profile():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "user_id is required"
            }), 400
        
        profile_data = models.User.get_user_profile(user_id)        
        if profile_data.get("first_connection"):
            profile_data["first_connection"] = profile_data["first_connection"].isoformat()
        if profile_data.get("last_connection"):
            profile_data["last_connection"] = profile_data["last_connection"].isoformat()
        
        return jsonify({
            "status": "200",
            "data": profile_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500



@endpoints_bp.route('/backend/user/profile', methods=['POST'])
def update_user_profile():
    try:
        user_id = request.args.get('user_id')
        role = request.args.get('role')
        affiliation = request.args.get('affiliation')
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "user_id is required"
            }), 400
        
        success = models.User.update_user_profile(user_id, role, affiliation)
        
        if success:
            return jsonify({
                "status": "200",
                "message": "Profile updated successfully"
            }), 200
        else:
            return jsonify({
                "status": "400",
                "error": "No valid data provided for update"
            }), 400
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500
    
    

@endpoints_bp.route('/backend/user/preferences', methods=['GET', 'OPTIONS'])
def get_user_preferences():
    """Get user preferences including text provider"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "user_id is required"
            }), 400
        
        preferences = models.User.get_user_preferences(user_id)
        return jsonify({
            "status": "200",
            "data": preferences
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/user/preferences', methods=['POST', 'OPTIONS'])
def save_user_preferences():
    """Save user preferences including text provider"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        text_provider = data.get('text_provider')
        
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "user_id is required"
            }), 400
        
        if text_provider and text_provider not in ["ollama", "openai"]:
            return jsonify({
                "status": "400",
                "error": "text_provider must be 'ollama' or 'openai'"
            }), 400
        
        success, message = models.User.update_user_preferences(user_id, text_provider=text_provider)
        
        if success:
            return jsonify({
                "status": "200",
                "message": message,
                "data": models.User.get_user_preferences(user_id)
            }), 200
        else:
            return jsonify({
                "status": "400",
                "error": message
            }), 400
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


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

        if not os.environ.get('OPENROUTER_API_KEY'):
            return jsonify({
                "status": "400",
                "error": "OpenRouter is not configured. Please set OPENROUTER_API_KEY in your .env file."
            }), 400

        import requests
        import json
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
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
        if not os.environ.get('OPENROUTER_API_KEY'):
            return jsonify({
                "status": "400",
                "error": "OpenRouter is not configured. Please set OPENROUTER_API_KEY in your .env file."
            }), 400
  
        import requests
        import json

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
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


