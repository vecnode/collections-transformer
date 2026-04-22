import logging

from bson.objectid import ObjectId
import bson.binary
import pandas as pd
import copy
import random
import datetime
import json
import os
import codecs
import base64
import tempfile
import urllib.request
import shutil
import concurrent.futures
from PIL import Image
import traceback
import pytz
from app.core.config import app_settings as settings
from app.infra.mongodb import get_db, get_grid_fs

db = get_db()
grid_fs = get_grid_fs()
if db is None or grid_fs is None:
    raise RuntimeError("MongoDB must be initialized before importing app.domain.models")

dataset_collection = db["dataset"]
item_collection = db["item"]
labelset_collection = db["labelset"]
label_collection = db["label"]
text_label_collection = db["text_label"]
embedding_collection = db["embedding"]
image_collection = db["image"]
analysis_history_collection = db["analysis_history"]
agent_collection = db["agent"]
user_collection = db["user"]

formatExamplesInsidePrompt = True
logger = logging.getLogger(__name__)


def _log_print(*args, **kwargs):
    logger.debug(" ".join(str(arg) for arg in args))


print = _log_print


def _read_uploaded_csv(csv_source):
  """Read CSV from a path, file-like object, or FastAPI UploadFile."""
  if hasattr(csv_source, "file"):
    stream = csv_source.file
    try:
      stream.seek(0)
    except Exception:
      pass
    return pd.read_csv(stream, sep=",", low_memory=False, na_filter=True)

  if hasattr(csv_source, "seek"):
    try:
      csv_source.seek(0)
    except Exception:
      pass

  return pd.read_csv(csv_source, sep=",", low_memory=False, na_filter=True)


# Inlined from model_parts/embedding.py
class Embedding():

  def create(item_id, content_id, content_type, image_data, subcontent_id=None):

    if content_type=="image":

      embeddings = []

      try:

        # Create smalled encoded version for thumbnails
        binary_encoded_image = bson.binary.Binary(image_data)

        embedding_obj = {
          "type":"image",
          "format":"bson",
          "value":binary_encoded_image,
          "item_id":item_id,
          "content_id":content_id,
          "subcontent_id":subcontent_id
        }

        embedding_id = embedding_collection.insert_one(embedding_obj).inserted_id
        embeddings.append(embedding_id)
      
      except Exception as e:
        print("error in creating BSON embedding")
        print(e)
        pass

      try:

        base64_encoded_image = base64.b64encode(image_data).decode('utf-8', 'ignore')

        embedding_obj = {
          "type":"image",
          "format":"base64",
          "value":base64_encoded_image,
          "item_id":item_id,
          "content_id":content_id,
          "subcontent_id":subcontent_id
        }

        embedding_id = embedding_collection.insert_one(embedding_obj).inserted_id
        embeddings.append(embedding_id)
      except Exception as e:
        print("error in creating Base64 embedding")
        print(e)

    return embeddings
  
  def get(embedding_id):
    embedding_res = embedding_collection.find({"_id":embedding_id},{"format":1,"value":1})
    embedding = list(embedding_res)[0]
    embedding['_id'] = str(embedding['_id'])
    return embedding
  
  def delete(item_id):
    embedding_collection.delete_many({"item_id":ObjectId(item_id)})




# Inlined from model_parts/labelset.py
class Labelset():

  # TODO refactor Labelset.get_all and Labelset.all into better-named more organised functions
  def all(user_id=None,includeLabels=False, includeNames=False,includeCount=False):
    print("Labelset.all")

    try:
      labelsets_list=[]

      if (user_id!=None):
        public_labelsets = labelset_collection.find({ "owner" : { "$exists" : False } }) # TODO change this to a system based on visibility
        private_labelsets = labelset_collection.find({ "$or":[ {  "owner" : user_id }, { "users" : { "$in" : [user_id] } }]})

        for labelset in list(private_labelsets):
          labelset['_id'] = str(labelset['_id'])
          labelset["dataset_id"] = str(labelset["dataset_id"])
          labelsets_list.append(labelset)

        for labelset in list(public_labelsets):
          labelset['_id'] = str(labelset['_id'])
          labelset["dataset_id"] = str(labelset["dataset_id"])
          labelsets_list.append(labelset)

      else:
        labelsets = labelset_collection.find()
        for labelset in list(labelsets):

          labelset['_id'] = str(labelset['_id'])
          labelset["dataset_id"] = str(labelset["dataset_id"])
          labelsets_list.append(labelset)

      for labelset in labelsets_list:
        # Convert ObjectIds to strings
        if isinstance(labelset.get('analyser_id'), ObjectId):
          labelset['analyser_id'] = str(labelset['analyser_id'])
        if isinstance(labelset.get('dataset_id'), ObjectId):
          labelset['dataset_id'] = str(labelset['dataset_id'])
        
        if (includeNames):
          dataset = Dataset.get(ObjectId(labelset["dataset_id"]))
          labelset["dataset_name"] = dataset["name"]

        if (includeCount):
          labels = Label.all(ObjectId(labelset['_id']))
          label_count = 0
          for l in labels:
            if len(str(l['value'])) > 0:
              label_count += 1
          labelset['label_count'] = label_count

    except Exception as e:
      print(e)

    return labelsets_list
  
  def get_all(user_id,dataset_id=None,label_type=None,includeLabels=False,includeNames=False,includeCount=False):

    print("Labelset.get_all")

    try:

      if label_type != None and dataset_id != None:
        ref = {"dataset_id":dataset_id, "label_type":label_type}
      elif dataset_id != None:
        ref = {"dataset_id":dataset_id}
      elif label_type != None:
        ref= {"label_type":label_type}
      else:
        ref = {}

      if (user_id!=None):
        ref1 = copy.deepcopy(ref)
        ref1["owner"] = user_id
        ref2 = copy.deepcopy(ref)
        ref2['users'] = { "$in" : [user_id] }
        labelsets_db_res = labelset_collection.find({"$or":[ref1,ref2]})
      else:
        labelsets_db_res = labelset_collection.find(ref)

      labelsets = list(labelsets_db_res)

      for labelset in labelsets:
        # Convert ObjectIds to strings first
        labelset["_id"] = str(labelset["_id"])
        if isinstance(labelset.get("dataset_id"), ObjectId):
          labelset["dataset_id"] = str(labelset["dataset_id"])
        if isinstance(labelset.get("analyser_id"), ObjectId):
          labelset["analyser_id"] = str(labelset["analyser_id"])
        labelset["label_type"] = str(labelset.get("label_type", "binary"))

        if (includeNames):
          dataset = Dataset.get(ObjectId(labelset["dataset_id"]))
          labelset["dataset_name"] = dataset["name"]

        if (includeCount):
          labels = Label.all(ObjectId(labelset['_id']))
          label_count = 0
          for l in labels:
            if len(str(l['value'])) > 0:
              label_count += 1
          labelset['label_count'] = label_count

    except Exception as e:
      print(e)
    return labelsets

  def get(dataset_id=None, labelset_id=None, includeLabels=False):

    try:
      if labelset_id!= None:
        labelset_id = labelset_id if isinstance(labelset_id,ObjectId) else ObjectId(labelset_id)
        labelset_db_res = labelset_collection.find({"_id":labelset_id})
      elif dataset_id!= None:
        labelset_db_res = labelset_collection.find({"dataset_id":dataset_id})

      labelset_res = list(labelset_db_res)
      if len(labelset_res) > 0:
        labelset = labelset_res[0]

        # Convert ObjectIds to strings
        labelset["_id"] = str(labelset["_id"])
        if isinstance(labelset.get("dataset_id"), ObjectId):
          labelset["dataset_id"] = str(labelset["dataset_id"])
        if isinstance(labelset.get("analyser_id"), ObjectId):
          labelset["analyser_id"] = str(labelset["analyser_id"])

        if includeLabels:
          labelset_id_obj = ObjectId(labelset["_id"])
          labels_db_res = label_collection.find({"labelset_id":labelset_id_obj})
          labels = list(labels_db_res)
          # Convert label ObjectIds to strings
          for label in labels:
            label["_id"] = str(label["_id"])
            if isinstance(label.get("dataset_id"), ObjectId):
              label["dataset_id"] = str(label["dataset_id"])
            if isinstance(label.get("item_id"), ObjectId):
              label["item_id"] = str(label["item_id"])
            if isinstance(label.get("labelset_id"), ObjectId):
              label["labelset_id"] = str(label["labelset_id"])
            if isinstance(label.get("analyser_id"), ObjectId):
              label["analyser_id"] = str(label["analyser_id"])
          labelset["labels"] = labels

        return labelset
      else:
        raise Exception("Invalid Labelset ID")

    except Exception as e:
      raise e


  def create(owner_id,dataset_id, labelset_type, name, analyser_id=None):
    labelset_obj = {
        "name": name,
        "label_type": labelset_type,
        "dataset_id" : dataset_id,
        "owner": owner_id,
        "version":"0",
        "versions":[
          {"id":"0"}
        ]
    }
    labelset_id = labelset_collection.insert_one(labelset_obj).inserted_id
    return labelset_id
  
  def delete(labelset_id):
    print("Deleting labelset " + str(labelset_id))
    # Delete Associated Labels
    labels_db_res = label_collection.find({"labelset_id":labelset_id})
    labels = list(labels_db_res)
    for label in labels:
      Label.delete('text',label["_id"])

    labelset_collection.delete_one({"_id":labelset_id})

  def update(labelset_id, data, isNewVersion):

    print("Labelset.update")

    l_id = ObjectId(labelset_id) if type(labelset_id) is str else labelset_id
    
    labelset = Labelset.get(None,labelset_id,True)

    labelset_collection.update_one({"_id":l_id},{"$set":data})
    
    if (isNewVersion):
      labelset_version = str(data["labelset_version"])
      labelset_collection.update_one({"_id":l_id},
      {"$set":{
        "version": labelset_version
      }})

      labelset_collection.update_one({"_id":l_id},
      {"$push":{
        "versions": {"id":labelset_version}
      }})

      #Make copies of the lables
      for label in labelset['labels']:
        Label.add_version(label['_id'],labelset_version)

      print("label versions added")

      labelset = Labelset.get(None,labelset_id,False)

    labelset_collection.update_one({"_id":l_id},
      {"$set":{
        "last_updated":datetime.datetime.now()
      }}
    )

    print("labelset update comeplete")


  def change_version(labelset_id, version_num):

    print("Labelset.change_version")
    print(version_num)

    l_id = labelset_id if isinstance(labelset_id,ObjectId) else ObjectId(labelset_id)

    labelset = Labelset.get(None,labelset_id,True)

    print("CHANGED VERSION")
    labelset_collection.update_one({"_id":l_id},
      {"$set":{
        "version": version_num
      }}
    )

    #Change label values to chosen version
    for label in labelset['labels']:
      Label.change_version(label['_id'],version_num)
    



# Inlined from model_parts/binary_label.py
class BinaryLabel():

  def create(
      labelset_id,
      item_id,
      content_type,
      content_ref,
      label_subtype=None, # positive or negative
      rationale=None,
      highlight=None,
      exclude=None
  ):
      print("creating binary label")
      content_level = 'content' if content_type == 'text' else 'subcontent'
      content_position = None

      item_db_res = item_collection.find({"_id":item_id},{"position":1})
      item = list(item_db_res)[0]
      content_position = item['position']

      labelset_db_res = labelset_collection.find({"_id":labelset_id})
      labelset = list(labelset_db_res)[0]

      version_obj = {
        "id":str(labelset['version']),
        "value":"" if label_subtype==None else (1 if label_subtype == 'positive' else 0),
        "rationale":"" if rationale==None else rationale,
        "highlight":"" if highlight==None else highlight,
        "exclude":"false" if exclude==None else exclude
      }

      label_obj = {
        "dataset_id": labelset["dataset_id"],
        "labelset_id": labelset_id,
        "item_id": item_id,
        "type": "binary",
        "content_level": content_level,
        "content_ref": content_ref,
        "content_position": content_position,
        "content_type": content_type, # Temporary for backwards compatibility, TODO remove
        "value":"" if label_subtype==None else (1 if label_subtype == 'positive' else 0),
        "rationale":"" if rationale==None else rationale,
        "highlight":"" if highlight==None else highlight,
        "exclude":"false" if exclude==None else exclude,
        "version": str(labelset['version']),
        "versions": []
      }
      
      label_obj["versions"].append(version_obj)
      
      print(label_obj)
      
      label_id = label_collection.insert_one(label_obj).inserted_id
      print("label_id " + str(label_id))
      return label_id

  def update(label,options):

    try:

      print("binaryLabel.UPDATE")

      label_subtype = options['label_subtype']
      ticked = options['ticked']

      if ticked != None:
        if ticked:
          if label_subtype == 'positive':
            BinaryLabel.tag_positive(label)
          else:
            BinaryLabel.tag_negative(label)  
        else:
          BinaryLabel.untag(label)
      label_subtype = options['label_subtype']
      ticked = options['ticked']

      if ticked != None:
        if ticked:
          if label_subtype == 'positive':
            BinaryLabel.tag_positive(label)
          else:
            BinaryLabel.tag_negative(label)  
        else:
          BinaryLabel.untag(label)

    except Exception as e:
      print("error in binarylabel.update")
      print(e)


  def tag_positive(label):
    
    try:

        label_collection.update_one({"_id":label["_id"]},
        {"$set":{
          "value":1
        }})

        labelset = Labelset.get(None,label['labelset_id'])
        Label.update_version(label['_id'],{"value":1},labelset['version'])

    except Exception as e:
      print("error in binarylabel.tagpositive")
      print(e)
  
  def tag_negative(label):

    try:
        label_collection.update_one({"_id":label["_id"]},
        {"$set":{
          "value":0
        }})

        labelset = Labelset.get(None,label['labelset_id'])
        Label.update_version(label['_id'],{"value":0},labelset['version'])

    except Exception as e:
      print("error in binarylabel.tagnegative")
      print(e)

  def untag(label):

    print("UNTAGGING")
    
    try:
      label_collection.delete_one({"_id":label["_id"]})
    except Exception as e:
      print("error in binarylabel.untag")
      print(e)




# Inlined from model_parts/score_label.py
class ScoreLabel():
  def create(
      labelset_id,
      item_id,
      content_type,
      content_ref,
      score=None, # between 1 and 5
      rationale=None,
      highlight=None,
      exclude=None
  ):
      print("creating score label")
      content_level = 'content' if content_type == 'text' else 'subcontent'
      content_position = None

      item_db_res = item_collection.find({"_id":item_id},{"position":1})
      item = list(item_db_res)[0]
      content_position = item['position']

      labelset_db_res = labelset_collection.find({"_id":labelset_id})
      labelset = list(labelset_db_res)[0]

      version_obj = {
        "id":str(labelset['version']),
        "value":"" if score==None else score,
        "rationale":"" if rationale==None else rationale,
        "highlight":"" if highlight==None else highlight,
        "exclude":"false" if exclude==None else exclude
      }

      label_obj = {
        "dataset_id": labelset["dataset_id"],
        "labelset_id": labelset_id,
        "item_id": item_id,
        "type": "score",
        "content_level": content_level,
        "content_ref": content_ref,
        "content_position": content_position,
        "content_type": content_type, # Temporary for backwards compatibility, TODO remove
        "value":"" if score==None else score,
        "rationale":"" if rationale==None else rationale,
        "highlight":"" if highlight==None else highlight,
        "exclude":"false" if exclude==None else exclude,
        "version":str(labelset['version']),
        "versions":[]
      }

      label_obj["versions"].append(version_obj)
      
      print(label_obj)
      
      label_id = label_collection.insert_one(label_obj).inserted_id
      print("label_id " + str(label_id))
      return label_id

  def update(label,options):

    print("scoreLabel.UPDATE")

    score = options['score']

    if score != None:
      if (score != "empty") and (score != ""):
        try:
          label_collection.update_one({"_id":label["_id"]},
          {"$set":{
            "value": score
          }})

          labelset = Labelset.get(None,label['labelset_id'])

          Label.update_version(label['_id'],{"value":score},labelset['version'])

        except Exception as e:
          print(e)
      else: 
          try:
            label_collection.delete_one({"_id":label["_id"]})
          except Exception as e:
            print(e)
                



# Inlined from model_parts/label.py
class Label():

  def get(label_id):
    try:  
      labels_db_res = label_collection.find({
        "_id":label_id
      })
      label = list(labels_db_res)[0]
      return label
    except Exception as e:
      return e
    
  def all(labelset_id, item_id=None, options={}):

    if item_id != None:
      label_db_res = label_collection.find({
        "labelset_id":labelset_id,
        "item_id":item_id
      })
    else:
      label_db_res = label_collection.find({
        "labelset_id":labelset_id
      })
   
    labels = list(label_db_res)

    if ("parse_ids" in options) and options["parse_ids"]:
      for label in labels:
        label["_id"] = str(label["_id"])
        label["dataset_id"] = str(label["dataset_id"])
        label["item_id"] = str(label["item_id"])
        if 'content_ref' in label:
          label["content_ref"] = str(label["content_ref"])
        label["labelset_id"] = str(label["labelset_id"])

    return labels


  def delete(type, label_id):
    ref = {"_id": ObjectId(label_id)}
    try:  
      label_collection.delete_one(ref)
    except Exception as e:
      return e
    
  def delete_all(labelset_id):
    ref = {"labelset_id": ObjectId(labelset_id)}
    try:  
      label_collection.delete_many(ref)
    except Exception as e:
      return e

  # Creates new labels or updates what is already there
  def update(
      label_type,
      labelset_id,
      item_id,
      content_ref,
      content_type,
      options={}
  ): 
    
    print("in Label.update")
    print(options)

    labelset = Labelset.get(None,labelset_id)

    try:
      label_db_res = label_collection.find({
        "labelset_id":labelset_id,
        "item_id":item_id,
        "content_type": content_type
      })

      label_res = list(label_db_res)
      if len(label_res) != 0:
        label = label_res[0]
        label_id = label["_id"] if isinstance(label["_id"],ObjectId) else ObjectId(label["_id"])
      else:
        label_id = ""

      if label_type == 'binary':

        if ('ticked' in options):
          if len(label_res) == 0: # No label exists, create one
            BinaryLabel.create(labelset_id,item_id,content_type,content_ref,options['label_subtype'])
          else:
            BinaryLabel.update(label,options)

        if ('rationale' in options):
          print("GOT rationale")
          print(options['rationale'])
          if len(label_res) == 0:
            BinaryLabel.create(labelset_id,item_id,content_type,content_ref,None,options['rationale'])
          else :
            label_collection.update_one({"_id":label_id},
              {"$set":{
                "rationale":options['rationale']
              }}
            )
            Label.update_version(label_id,{"rationale":options['rationale']},labelset['version'])

        if ('highlight' in options):
          if len(label_res) == 0:
            BinaryLabel.create(labelset_id,item_id,content_type,content_ref,None,None,options['highlight'])
          else :
            label_collection.update_one({"_id":label_id},
              {"$set":{
                "highlight":options['highlight']
              }}
            ) 
            Label.update_version(label_id,{"highlight":options['highlight']},labelset['version'])

        if ('exclude' in options):
          if len(label_res) == 0:
            BinaryLabel.create(labelset_id,item_id,content_type,content_ref,None,None,None,options['exclude'])
          else :
            label_collection.update_one({"_id":label_id},
              {"$set":{
                "exclude":options['exclude']
              }}
            ) 
            Label.update_version(label_id,{"exclude":options['exclude']},labelset['version'])
        
      if label_type == 'score':

        if ('score' in options):
          if len(label_res) == 0: # No label exists, create one
            ScoreLabel.create(labelset_id,item_id,content_type,content_ref,options['score'])
          else:
            ScoreLabel.update(label,options)

        if ('rationale' in options):
          if len(label_res) == 0:
            ScoreLabel.create(labelset_id,item_id,content_type,content_ref,None,options['rationale'])
          else :
            label_collection.update_one({"_id":label_id},
              {"$set":{
                "rationale":options['rationale']
              }}
            )
            Label.update_version(label_id,{"rationale":options['rationale']},labelset['version'])

        if ('highlight' in options):
          if len(label_res) == 0:
            ScoreLabel.create(labelset_id,item_id,content_type,content_ref,None,None,options['highlight'])
          else :
            label_collection.update_one({"_id":label_id},
              {"$set":{
                "highlight":options['highlight']
              }}
            )
            Label.update_version(label_id,{"highlight":options['highlight']},labelset['version'])

        if ('exclude' in options):
          if len(label_res) == 0:
            ScoreLabel.create(labelset_id,item_id,content_type,content_ref,None,None,options['exclude'])
          else :
            label_collection.update_one({"_id":label_id},
              {"$set":{
                "exclude":options['exclude']
              }}
            )
            Label.update_version(label_id,{"exclude":options['exclude']},labelset['version'])

      Labelset.update(labelset_id,{},False)
    
    except Exception as e:
      print("error in label.update ")
      print(e)

  # Update details of an existing label version
  def update_version(label_id,data,version_num):

    try:

      label = Label.get(label_id)

      # Get existing verison obj
      version_obj_res = [v for v in label['versions'] if v['id'] == str(version_num)]
      print(len(version_obj_res))

      if (len(version_obj_res) > 0):

        if ("value" in data):
          # Update version record
          label_collection.update_one({"_id":label['_id'],"versions.id":version_num},{
            "$set":{
              "versions.$.value":data['value']
            }
          })
        
        if ("highlight" in data):
          # Update version record
          label_collection.update_one({"_id":label['_id'],"versions.id":version_num},{
            "$set":{
              "versions.$.highlight":data['highlight']
            }
          })
        
        if ("rationale" in data):
          # Update version record
          label_collection.update_one({"_id":label['_id'],"versions.id":version_num},{
            "$set":{
              "versions.$.rationale":data['rationale']
            }
          })

        if ("exclude" in data):
          # Update version record
          label_collection.update_one({"_id":label['_id'],"versions.id":version_num},{
            "$set":{
              "versions.$.exclude":data['exclude']
            }
          })


    except Exception as e:
      print("error in label.update_version ")
      print(e)
  
  # Change label values to a different stored version
  def change_version(label_id,version_num):

    try:
      label = Label.get(label_id)

      update_obj = {}

      # If switching versions to an existing version, select it
      version_obj_res = [v for v in label['versions'] if str(v['id']) == str(version_num)]
      if (len(version_obj_res) > 0):
        version_obj=version_obj_res[0]
        update_obj={
          "value":version_obj["value"],
          "rationale":version_obj['rationale'],
          "highlight":version_obj["highlight"]
        }

      # if no version data saved for this version num, set to blank
      else:

        update_obj={
          "value":"",
          "rationale":"",
          "highlight":""
        }

      label_collection.update_one({"_id":label['_id']},{
        "$set":{
          "version":version_num
        }
      }) 

      label_collection.update_one({"_id":label['_id']},{
        "$set":update_obj
      }) 

    except Exception as e:
      print("error in label.update_version ")
      print(e)

  def add_version(label_id,new_version_num):
      
    label = Label.get(label_id)

    # update vals
    update_obj={
      "id": new_version_num,
      "value":label["value"],
      "rationale":label['rationale'] if ("rationale" in label) else "",
      "highlight":label["highlight"] if ("highlight" in label) else "",
      "exclude":label["exclude"] if ("exclude" in label) else ""
    }

    # Create new version record
    label_collection.update_one({"_id":label['_id']},{
      "$push":{
        "versions":update_obj
      }
    })

    #Update version ref
    label_collection.update_one({"_id":label['_id']},{
      "$set":{
        "version":new_version_num
      }
    }) 

    label = Label.get(label_id)

  def update_version_value(label, value):
    
    label = Label.get(label["_id"])

    matching_version = [v for v in label['versions'] if str(v['id']) == str(label['version'])]

    if (len(matching_version)==0):
      update_ref = {
        "_id": label["_id"]
      }

      label_collection.update_one(update_ref,
      {"$push":
        {
        "versions":{
          "id":label['version'],
          "value":value
        }
      }
      })
    else:
      print("updating current version")
      print(label['version'])
      # Update current version record 
      update_ref = {
        "_id": label["_id"],
        "versions.id":label['version']
      }
      label_collection.update_one(update_ref,
      {"$set":{
        "versions.$.value":value
      }})

  def deleteTextLabels(item_id=None, analyser_id=None):

    if item_id!=None:
      text_label_collection.delete_many({
        "item_id": item_id,
        "analyser_id": "null" if analyser_id == None else analyser_id
      })
    elif item_id==None and analyser_id!=None:
        text_label_collection.delete_many({
          "analyser_id": analyser_id
        })




# Inlined from model_parts/dataset.py
class Dataset():
  
  def get_all(user_id):

    public_datasets = dataset_collection.find({ "owner" : { "$exists" : False } }) # TODO change this to a system based on visibility
    private_datasets = dataset_collection.find({ "$or":[ {  "owner" : user_id }, { "users" : { "$in" : [user_id] } }]})

    datasets_list = []
    for dataset in list(private_datasets):
      dataset['_id'] = str(dataset['_id'])
      datasets_list.append(dataset)

    for dataset in list(public_datasets):
      dataset['_id'] = str(dataset['_id'])
      datasets_list.append(dataset)

    return datasets_list

  def get(dataset_id, includeArtworks=False, includeEmbeddings=False):
    try: 

      dataset_id = dataset_id if isinstance(dataset_id,ObjectId) else ObjectId(dataset_id)

      dataset_db_res = dataset_collection.find({"_id":dataset_id})
      # Extracting obj from mongo cursor
      dataset_res = list(dataset_db_res)
      dataset = dataset_res[0]

      dataset['_id'] = str(dataset['_id'])
      
      if (includeArtworks):
        include = {
          "content":1,
          "text":1,
          "position":1,
          "object_id":1
        } 

        artworks_db_res = item_collection.find({
          "dataset_id": dataset_id
        },include)
        artworks_list= list(artworks_db_res)
        artworks = []

        for item in artworks_list:
          formatted_item = Item.getFullItem(item, includeEmbeddings)

          artworks.append(formatted_item)

        dataset['artworks'] = artworks

      return dataset
    
    except Exception as e:
      print(e)
      raise e

  def create(owner_id,dataset_type,dataset_name,text_data_file,image_data_file,text_image_data_file,image_upload_type=None):
            
      dataset_id = None
      
      if dataset_type == "text":
        dataset_id = Dataset.create_text_dataset(owner_id,dataset_name,text_data_file)
      elif dataset_type == "image":
        dataset_id = Dataset.create_image_dataset(owner_id,dataset_name,image_data_file,image_upload_type)
      elif dataset_type == "textimage":
        if image_upload_type == 'image_file':
          dataset_id = Dataset.create_text_and_image_dataset(owner_id,dataset_name,text_data_file,image_data_file,None,image_upload_type)
        else:
          dataset_id = Dataset.create_text_and_image_dataset(owner_id,dataset_name,None,image_data_file,text_image_data_file,image_upload_type)

      return dataset_id
  
  
  def create_text_dataset(owner_id,dataset_name,data_file):
    df = _read_uploaded_csv(data_file)
    texts = list(df['text'])

    if 'object_id' in df:
      object_id = list(df['object_id'])

    dataset = {
      "name": dataset_name,
      "type":"text",
      "status": 0,
      "artwork_count": len(texts),
      "owner": owner_id,
      "upload_time": datetime.datetime.now()
    }

    #insert dataset and get dataset_ID
    dataset_id = dataset_collection.insert_one(dataset).inserted_id

    #add items
    item_list = []
    itt = 0

    for i, text in enumerate(texts):

      content = [
          {
              "content_type": "text",
              "content_value": {
                  "text": text,
                  "embedding_id": None
              },
              "subcontent": None
          }
      ]

      item = {
          "content": content,
          "dataset_id": dataset_id,
          "position": itt,
          "analyser_id": None,
          "object_id": object_id[i] if 'object_id' in df else None
      }

      item_list.append(item)
      itt = itt + 1

    #bulk insert items from array
    Item.create_all(item_list)

    #update dataset status
    query = { '_id': dataset_id }
    newvalue = { "$set": { 'status': 1 } }
    dataset_collection.update_one(query, newvalue)

    return dataset_id
  

  def create_image_dataset(owner_id,dataset_name,images,image_upload_type):
    try:

      if image_upload_type == 'image_link':
        df = _read_uploaded_csv(images)
        df['id'] = df.index.astype(str)
        image_links = df[['id', 'image']].to_dict('records')
        images, error_links = Dataset.download_image_links(image_links)
        if 'object_id' in df:
          #remove error links from df
          df = df[~df['id'].isin(error_links)]
          object_ids = list(df['object_id'])
        files = sorted([f'{images}/{f}' for f in os.listdir(images)])
      else:
        files = images

      dataset = {
        "name": dataset_name,
        "type":"image",
        "status": 0,
        "artwork_count": len(files),
        "owner": owner_id,
        "upload_time": datetime.datetime.now()
      }

      #insert dataset and get dataset_ID
      dataset_id = dataset_collection.insert_one(dataset).inserted_id

      #add items
      item_list = []
      itt = 0

      for i, image in enumerate(files):

        content = [
          {
              "content_type": "image",
              "content_value": {
                  "image_storage_id":"",
                  "text":"",
                  "embedding_ids":[]
              },
              "subcontent": None
          }
        ]

        item = {
            "content": content,
            "dataset_id": dataset_id,
            "position": itt,
            "analyser_id": None,
            "object_id": object_ids[i] if (image_upload_type == 'image_link' and 'object_id' in df) else None
        }

        item_list.append(item)
        itt = itt + 1

      #bulk insert items from array
      item_ids = Item.create_all(item_list)

      # Store image data
      marker = len(item_ids)/10
      for i, id in enumerate(item_ids):
        item = Item.get(id)
        if (int(i)/marker).is_integer():
            print(f"{int(int(i)/marker)}0% complete")
        for index, content in enumerate(item['content']):
          if content["content_type"] == "image":
            if image_upload_type == 'image_file':
              image = images[i]
              filename = image.filename
            else:
              image = open(files[i], 'rb')
              filename = files[i].split('/')[-1]
            raw_image_data = image.read()
            ## Create Embeddings
            embedding_ids = Embedding.create(id,index,content["content_type"],raw_image_data,content["subcontent"])
            Item.update(id,{"embedding_ids":embedding_ids},index)
            ## Store image
            image_storage_id = grid_fs.put(raw_image_data, filename=filename)
            Item.update(id,{"image_storage_id":image_storage_id,"text":filename},index)
            image.close()


      #update dataset status
      query = { '_id': dataset_id }
      newvalue = { "$set": { 'status': 1 } }
      dataset_collection.update_one(query, newvalue)

      # delete temp_dir
      if image_upload_type == 'image_link':
        shutil.rmtree(images) 
        return dataset_id, error_links
      
      else:
        return dataset_id
    
    except Exception as e:
      print(e)

  def create_text_and_image_dataset(owner_id,dataset_name,text,images,text_and_images,image_upload_type):
    try:
      if image_upload_type == 'image_file':
        df = _read_uploaded_csv(text)
        files = images
      else: 
        df = _read_uploaded_csv(text_and_images)
        #make id column out of urls 
        df['id'] = df.index.astype(str)
        image_links = df[['id', 'image']].to_dict('records')
        images, error_links = Dataset.download_image_links(image_links)
        #remove error links from df
        df = df[~df['id'].isin(error_links)]
        files = sorted([f'{images}/{f}' for f in os.listdir(images)]) #make sure same order as os.walk

      texts = list(df['text'])
      if 'object_id' in df:
        object_ids = list(df['object_id'])

      dataset = {
        "name": dataset_name,
        "type":"textimage",
        "status": 0,
        "artwork_count": 0,
        "owner": owner_id,
        "upload_time": datetime.datetime.now()
      }

      #insert dataset and get dataset_ID
      dataset_id = dataset_collection.insert_one(dataset).inserted_id

      #add items
      item_list = []
      itt = 0

      for i, image in enumerate(files):
        
        if 'filename' in df and image_upload_type == 'image_file': 
          img_filename = image.filename if len(image.filename.split('.')) == 1 else ".".join(image.filename.split('.')[:-1])
          text_search = df.loc[df['filename'] == img_filename]

          if not text_search.empty:
            text = text_search['text'].values[0]
            object_id = str(text_search['object_id'].values[0]) if 'object_id' in df else None
          else:
            continue

        else:
          text = texts[i] if i < len(texts) else ""
          object_id = object_ids[i] if 'object_id' in df else None

        content = [
          {
              "content_type": "image",
              "content_value": {
                  "image_storage_id":"",
                  "text":"",
                  "embedding_ids":[]
              },
              "subcontent": None
          },
          {
              "content_type": "text",
              "content_value": {
                  "text": text,
                  "embedding_id": None
              },
              "subcontent": None
          }
        ]

        item = {
            "content": content,
            "dataset_id": dataset_id,
            "position": itt,
            "analyser_id": None,
            "object_id": object_id
        }

        item_list.append(item)
        itt = itt + 1

      # bulk insert items from array
      item_ids = Item.create_all(item_list)

      #update dataset item num
      dataset_collection.update_one({"_id":dataset_id},{"$set":{"artwork_count":len(item_list)}})

      # Store image data
      marker = round(len(item_ids)/10)
      for i, id in enumerate(item_ids):
        item = Item.get(id)
        if (int(i)/marker).is_integer():
          print(f"{int(int(i)/marker)}0% complete")
        for index, content in enumerate(item['content']):
          if content["content_type"] == "image":
            if image_upload_type == 'image_file':
              image = images[i]
              filename = image.filename
            else:
              image = open(files[i], 'rb')
              filename = files[i].split('/')[-1]
            raw_image_data = image.read()
            ## Create Embeddings
            embedding_ids = Embedding.create(id,index,content["content_type"],raw_image_data,content["subcontent"])
            Item.update(id,{"embedding_ids":embedding_ids},index)
            ## Store image
            image_storage_id = grid_fs.put(raw_image_data, filename=filename)
            Item.update(id,{"image_storage_id":image_storage_id,"text":filename},index)
            image.close()
      #update dataset status
      Dataset.set_status(dataset_id,1)

      #delete temp_dir
      if image_upload_type == 'image_link':
        shutil.rmtree(images) 
        return dataset_id, error_links
      else:
        return dataset_id
    
    except Exception as e:
      print(e)


  def download_image(image_link, dir):
    filename = f"{image_link['id']}.jpg"
    fullpath = f'{dir}/{filename}'
    urllib.request.urlretrieve(image_link['image'], fullpath)
    #compress image and save as jpeg
    size = 1024, 1024
    image = Image.open(fullpath)
    image.thumbnail(size, "JPEG", quality=95)
    image.save(fullpath)

  def download_image_links(image_links):
    temp_dir = tempfile.mkdtemp()
    with concurrent.futures.ThreadPoolExecutor() as executor:
      error_links = []
      for i in image_links:
        try:
          executor.submit(Dataset.download_image,i, temp_dir)
        except Exception as e:
          error_links.append(i['id'])
          print(f"Error downloading: {i['id']}")
          print(e)
      executor.shutdown()
    
    return temp_dir, error_links

  def get_status(dataset_id):
    try:
      dataset = dataset_collection.find_one({"_id":ObjectId(dataset_id)},{"status":1})
      return dataset['status']
    except Exception as e:
      print(e)

  def set_status(dataset_id,dataset_status):
    try:
      dataset_collection.update_one({"_id":ObjectId(dataset_id)},{"$set":{"status":dataset_status}})
    except Exception as e:
      print(e)

  def update(dataset_id,data):
    try:
      d_id = ObjectId(dataset_id) if type(dataset_id) is str else dataset_id
      dataset_collection.update_one({"_id":d_id},{"$set":data})
    except Exception as e:
      print(e)

  def delete(dataset_id): # WIP

    #update dataset status
    Dataset.set_status(dataset_id,-1)

    # Get dataset type
    dataset = dataset_collection.find_one({"_id":ObjectId(dataset_id)})
    dataset_type = dataset['type']

    # Delete associated items
    items_db_res = item_collection.find({"dataset_id":ObjectId(dataset_id)})
    items = list(items_db_res)

    marker = round(len(items)/10)
    for i, item in enumerate(items):
      if (int(i)/marker).is_integer():
          print(f"{int(int(i)/marker)}0% complete")

      Item.delete(item['_id'])

      if dataset_type == 'image':
        Embedding.delete(item['_id'])

        file_id = next((x for x in item["content"] if x['content_type'] == 'image'))['content_value']['image_storage_id']

        grid_fs.delete(file_id)
      

    # Delete labelsets
    labelset_db_res = labelset_collection.find({"dataset_id":ObjectId(dataset_id)})
    labelsets = list(labelset_db_res)
    for labelset in labelsets:
      Labelset.delete(labelset['_id'])

    dataset_collection.delete_one({"_id": ObjectId(dataset_id)}) # Delete dataset





# Inlined from model_parts/item.py
class Item():

  def create(content, position, dataset_id):
     
    item_obj = {
      "dataset_id": dataset_id,
      "position": position,
      "content": content
    }

    item_id = item_collection.insert_one(item_obj).inserted_id
    return item_id

  def create_all(item_list):
    result = item_collection.insert_many(item_list)
    return result.inserted_ids

  def update(item_id,data,content_index=None):
    id = item_id if isinstance(item_id,ObjectId) else ObjectId(item_id)
    query = { '_id': id }
    if content_index!=None:
      if 'embedding_ids' in data:
        newvalue = { "$set": { 'content.'+str(content_index)+'.content_value.embedding_ids': data['embedding_ids']} }
        item_collection.update_one(query, newvalue, upsert=True)  
      if 'image_storage_id' in data:
        newvalue = { "$set": { 'content.'+str(content_index)+'.content_value.image_storage_id': data['image_storage_id']} }
        item_collection.update_one(query, newvalue, upsert=True)  
      if 'text' in data:
        newvalue = { "$set": { 'content.'+str(content_index)+'.content_value.text': data['text']} }
        item_collection.update_one(query, newvalue, upsert=True)  

  def get(item_id):
    item_db_res = item_collection.find({"_id":ObjectId(item_id)})
    item = list(item_db_res)[0]
    return item

  def getFullItem(item,includeEmbeddings=False):

    formatted_item = {}
    formatted_item['_id'] = str(item['_id'])
    formatted_item['predicted'] = None
    formatted_item['position'] = item.get('position', 0)
    formatted_item['object_id'] = item.get('object_id', None)
    formatted_item['content'] = item['content'] if 'text' not in item else item['text']
    formatted_item['subcontent'] = item['content'][0].get('subcontent', None) if item.get('content') and len(item.get('content', [])) > 0 else None

    for c in formatted_item['content']:
      if c['content_type'] == "image":
        c['content_value']['image_storage_id'] = str(c['content_value']['image_storage_id'])
        c['content_value']['embeddings'] = []
        for index, e in enumerate(c['content_value']['embedding_ids']):
          if (includeEmbeddings):
            c['content_value']['embeddings'].append(Embedding.get(c['content_value']['embedding_ids'][index]))
          c['content_value']['embedding_ids'][index] = str(e)
    
    return formatted_item
  
  def getImage(item_id,image_storage_id):
    isid = image_storage_id if isinstance(image_storage_id, ObjectId) else ObjectId(image_storage_id)
    img = grid_fs.get(isid)
    encoded_img = codecs.encode(img.read(), 'base64')
    return encoded_img

  def delete(item_id): # Expects ObjectID not string
      item_collection.delete_one({"_id":ObjectId(item_id)})




# Inlined from model_parts/user.py
class User():
    def record_connection(user_id, event_type='login', should_update_connection=True):
        """Record a user connection with timestamp and event type"""
        london_tz = pytz.timezone('Europe/London')
        current_time = datetime.datetime.now(london_tz)
        
        # Check if user exists
        existing_user = user_collection.find_one({"user_id": user_id})
        
        if existing_user:
            # Store the current last_connection as previous_connection before updating
            previous_connection = existing_user.get("last_connection")
            
            # Update data
            update_data = {
                "previous_connection": previous_connection,
                "last_event_type": event_type,
                "last_event_time": current_time
            }
            
            # Only update last_connection for certain events
            if should_update_connection:
                update_data["last_connection"] = current_time
            
            user_collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
        else:
            # Create new user record
            user_obj = {
                "user_id": user_id,
                "first_connection": current_time,
                "last_connection": current_time if should_update_connection else None,
                "previous_connection": None,
                "last_event_type": event_type,
                "last_event_time": current_time
            }
            user_collection.insert_one(user_obj)
    
    def get_last_connection(user_id):
        """Get the last connection time for a user"""
        user = user_collection.find_one({"user_id": user_id})
        if user:
            return user.get("last_connection")
        return None

    def get_user_profile(user_id):
        """Get user profile data including role and affiliation"""
        user = user_collection.find_one({"user_id": user_id})
        if user:
            # Use previous_connection if available, otherwise fall back to last_connection
            last_connection = user.get("previous_connection") or user.get("last_connection")
            
            return {
                "role": user.get("role", ""),
                "affiliation": user.get("affiliation", ""),
                "first_connection": user.get("first_connection"),
                "last_connection": last_connection
            }
        return {
            "role": "",
            "affiliation": "",
            "first_connection": None,
            "last_connection": None
        }

    def update_user_profile(user_id, role=None, affiliation=None):
        """Update user profile data"""
        update_data = {}
        if role is not None:
            update_data["role"] = role
        if affiliation is not None:
            update_data["affiliation"] = affiliation
        
        if update_data:
            user_collection.update_one(
                {"user_id": user_id},
                {"$set": update_data},
                upsert=True
            )
            return True
        return False
    
    def get_user_preferences(user_id):
        """Get user preferences (Ollama-only text provider)."""
        user = user_collection.find_one({"user_id": user_id})
        if user:
            preferences = user.get("preferences", {})
            text_provider = preferences.get("text_provider", "ollama")
            return {
                "text_provider": text_provider
            }
        return {
            "text_provider": "ollama"  # Default
        }
    
    def update_user_preferences(user_id, text_provider=None):
        """Update user preferences"""
        user = user_collection.find_one({"user_id": user_id})
        preferences = user.get("preferences", {}) if user else {}
        
        if text_provider is not None:
            if text_provider != "ollama":
                return False, "Invalid text provider. Must be 'ollama'"
            preferences["text_provider"] = text_provider
        
        update_data = {"preferences": preferences}
        user_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data},
            upsert=True
        )
        return True, "Preferences updated successfully"





# Inlined from model_parts/analysis_history.py
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




# Inlined from model_parts/agent.py
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
                    "model": settings.ollama_model_option
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




