from api import db, grid_fs

from bson.objectid import ObjectId
import bson.binary
import json
from . import llm_modelling as llm
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

category_collection = db["category"] 
analyser_collection = db["classifier"] 
dataset_collection = db["dataset"] 
item_collection = db["item"] 
labelset_collection = db["labelset"]
label_collection = db["label"]
text_label_collection = db["text_label"]
resultset_collection = db["resultset"]
embedding_collection = db["embedding"]
image_collection = db["image"]
analysis_history_collection = db["analysis_history"]
agent_collection = db["agent"]

formatExamplesInsidePrompt = True

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

    #Remove reference from all Analysers
    analysers_db_res = analyser_collection.find({})
    for analyser in list(analysers_db_res):
      analyser_versions = [v for v in analyser['versions'] if ('versions' in analyser) and v!=None]
      new_versions = []
      for v in analyser_versions:
        if ('labelset_id' in v) and (v['labelset_id'] != str(labelset_id)):
          new_versions.append(v)
      analyser_collection.update_one({"_id":analyser['_id']},{"$set":{"versions":new_versions}})

    analyser_collection.update_many({"labelset_id":labelset_id},{
      "$set": {
        "labelset_id":"",
        "prompt":"",
        "example_refs":[],
        "examples":[],
        "sample_ids":[],
        "predictions":[],
        "accuracy":""
      }
    })

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
  
  def copy_all(labelset_id, new_labelset_id, item_id=None, options={}):
    try:

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
    
      for label in labels:

        label.update({"version":"0"})
        label.update({"versions":[{
          "id":"0",
          "value":label['value'] if ('value' in label) else "",
          "highlight":label['highlight'] if ("highlight" in label) else "",
          "rationale":label['rationale'] if ("rationale" in label) else "",
          "exclude":label['exclude'] if ("exclude" in label) else "false"
        }]})

        label.pop("_id")
        label.update({
          "labelset_id": new_labelset_id
        })
        label_collection.insert_one(label)

    except Exception as e:
      print(e)
      raise e


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
    df = pd.read_csv(data_file, sep=",", low_memory=False, na_filter=True)
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
        df = pd.read_csv(images, sep=",", low_memory=False, na_filter=True)
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
        df = pd.read_csv(text, sep=",", low_memory=False, na_filter=True)
        files = images
      else: 
        df = pd.read_csv(text_and_images, sep=",", low_memory=False, na_filter=True)
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

  def get_test_set(dataset_id):
    dataset = Dataset.get(dataset_id, True, True)
    # Loads up all the data for this classifier along with embeddings for model predictions
    ids = []
    texts = []
    bert_embeddings = {}
    for artwork in dataset['artworks']:
      ids.append(artwork.id)
      texts.append(artwork.text)
      bert_embeddings[artwork.text] = artwork.bert_embedding
    return ids, texts, bert_embeddings


class Category():

  def get(category_id):
    category_id = category_id if isinstance(category_id,ObjectId) else ObjectId(category_id)
    category_db_entry = category_collection.find({"_id":category_id})
    
    # Extracting obj from mongo cursor
    category_res = list(category_db_entry)
    category = category_res[0]
    category['_id'] = str(category['_id'])

    return category
  
  def get_all(user_id):
    public_categories = category_collection.find({ "owner" : { "$exists" : False } }) # TODO change this to a system based on visibility
    private_categories = category_collection.find({ "owner" : user_id })

    categories_list = []
    for category in list(private_categories):
      category['_id'] = str(category['_id'])
      categories_list.append(category)

    for category in list(public_categories):
      category['_id'] = str(category['_id'])
      categories_list.append(category)

    return categories_list





class Analyser():

  def create(
      owner_id, 
      analyser_type,
      name, 
      task_description, 
      labelling_guide, 
      dataset_id, 
      labelset_id, 
      category_id,
      auto_select_examples=None,
      chosen_example_ids=None,
      num_examples=None,
      example_start_index=None,
      example_end_index=None
  ):
    try:

      if (dataset_id!= None):
        dataset = Dataset.get(dataset_id)
        analyser_format = dataset['type']
      else:
        analyser_format = "" 

      prompt, prompt_examples, example_ids = Analyser.createLLMprompt(
        analyser_type,
        analyser_format,
        task_description,
        labelling_guide,
        dataset_id,
        labelset_id,
        formatExamplesInsidePrompt,
        auto_select_examples,
        chosen_example_ids,
        num_examples,
        example_start_index,
        example_end_index
      )

      if (labelset_id!= None):
        labelset = Labelset.get(None,labelset_id)

        labelset_version = str(int(max(int(v['id']) for v in labelset['versions'] if v!=None)) + 1)

        Labelset.update(labelset_id,{"labelset_version":labelset_version},True)

      analyser_args = {
        "name": name,
        "dataset_id":ObjectId(dataset_id) if (dataset_id!= None) else "",
        "category_id": ObjectId(category_id) if (category_id!= None) else "",
        "labelset_id":labelset_id if (labelset_id!= None) else "",
        "labelset_version":"0" if (labelset_id!= None) else "",
        "analyser_type": analyser_type,
        "analyser_format": analyser_format,
        "task_description": task_description,
        "labelling_guide": labelling_guide,
        "examples": prompt_examples,
        "example_refs": json.loads(example_ids) if type(example_ids) is str else example_ids,
        "prompt":prompt,
        "sample_ids":[],
        "version":0,
        "owner": owner_id,
        "versions": [{
          "id": 0,
          "dataset_id":ObjectId(dataset_id) if (dataset_id!= None) else "",
          "category_id": ObjectId(category_id) if (category_id!= None) else "",
          "labelset_id":labelset_id if (labelset_id!= None) else "",
          "labelset_version": "0" if (labelset_id!= None) else "",
          "analyser_type": analyser_type,
          "analyser_format": analyser_format,
          "task_description": task_description,
          "labelling_guide": labelling_guide,
          "examples": prompt_examples,
          "example_refs": json.loads(example_ids) if type(example_ids) is str else example_ids,
          "sample_ids":[],
          "prompt":prompt,
          "last_updated" : datetime.datetime.now()
        }]
      }

      # #insert dataset and get dataset_ID
      analyser_res = analyser_collection.insert_one(analyser_args).inserted_id
      analyser_id = str(analyser_res)

      return analyser_id
    
    except Exception as e:
      print(e)

  def get(analyser_id, includeNames=True, includeVersions=False):

    analyser_id = analyser_id if isinstance(analyser_id,ObjectId) else ObjectId(analyser_id)

    try:
      
      filter = {"versions":0} if not includeVersions else {}

      analyser_db_res = analyser_collection.find({
        "_id": analyser_id
      },filter)

      analyser_res = list(analyser_db_res)
      if len(analyser_res) == 0:
        raise Exception(f"Analyser with id {analyser_id} not found")
      
      analyser = analyser_res[0]
      analyser['_id'] = str(analyser['_id'])

      if (includeNames):

        dataset_id = analyser.get('dataset_id')
        if dataset_id and dataset_id != "" and str(dataset_id).strip() != "":
          try:
            # Check if it's a valid ObjectId before trying to convert
            dataset_id_str = str(dataset_id).strip()
            if isinstance(dataset_id, ObjectId) or (len(dataset_id_str) == 24 and ObjectId.is_valid(dataset_id_str)):
              dataset = Dataset.get(dataset_id, False, False)
              if dataset:
                analyser['dataset_name']=dataset['name']
          except Exception as e:
            print(f"Could not lookup Dataset for analyser {analyser_id}: {e}")

        category_id = analyser.get('category_id')
        if category_id and category_id != "" and str(category_id).strip() != "":
          try:
            # Check if it's a valid ObjectId before trying to convert
            category_id_str = str(category_id).strip()
            if isinstance(category_id, ObjectId) or (len(category_id_str) == 24 and ObjectId.is_valid(category_id_str)):
              category = Category.get(category_id)
              if category:
                analyser['category_name']=category['name']
          except Exception as e:
            print(f"Could not lookup Category for analyser {analyser_id}: {e}")

        labelset_id = analyser.get('labelset_id')
        if labelset_id and labelset_id != "" and str(labelset_id).strip() != "":
          try:
            # Check if it's a valid ObjectId before trying to convert
            labelset_id_str = str(labelset_id).strip()
            if isinstance(labelset_id, ObjectId) or (len(labelset_id_str) == 24 and ObjectId.is_valid(labelset_id_str)):
              labelset = Labelset.get(None, labelset_id)
              if labelset:
                analyser['labelset_name'] = labelset['name']
          except Exception as e:
            print(f"Could not lookup Labelset for analyser {analyser_id} - Likely labelset deleted but analyser reference remains: {e}")

      if (includeVersions):
        for version in analyser.get('versions', []):
          if version != None:
            # Convert all ObjectId fields in version
            for key in ['dataset_id', 'category_id', 'labelset_id']:
              if key in version and isinstance(version[key], ObjectId):
                version[key] = str(version[key])
            # Convert any other ObjectIds in version dict
            for key, value in version.items():
              if isinstance(value, ObjectId):
                version[key] = str(value)
              elif isinstance(value, list):
                version[key] = [str(item) if isinstance(item, ObjectId) else item for item in value]

      # Safely convert all ObjectId fields to strings
      # Convert dataset_id
      if analyser.get('dataset_id') is not None:
        if isinstance(analyser['dataset_id'], ObjectId):
          analyser['dataset_id'] = str(analyser['dataset_id'])
        elif analyser['dataset_id'] != "":
          analyser['dataset_id'] = str(analyser['dataset_id'])
        else:
          analyser['dataset_id'] = ""
      else:
        analyser['dataset_id'] = ""
        
      # Convert category_id
      if analyser.get('category_id') is not None:
        if isinstance(analyser['category_id'], ObjectId):
          analyser['category_id'] = str(analyser['category_id'])
        elif analyser['category_id'] != "":
          analyser['category_id'] = str(analyser['category_id'])
        else:
          analyser['category_id'] = ""
      else:
        analyser['category_id'] = ""
        
      # Convert labelset_id
      if analyser.get('labelset_id') is not None:
        if isinstance(analyser['labelset_id'], ObjectId):
          analyser['labelset_id'] = str(analyser['labelset_id'])
        elif analyser['labelset_id'] != "":
          analyser['labelset_id'] = str(analyser['labelset_id'])
        else:
          analyser['labelset_id'] = ""
      else:
        analyser['labelset_id'] = ""
      
      # Convert any other ObjectId fields that might exist (owner, example_refs, sample_ids, etc.)
      for key, value in analyser.items():
        if isinstance(value, ObjectId):
          analyser[key] = str(value)
        elif isinstance(value, list):
          # Check list items for ObjectIds (e.g., example_refs, sample_ids)
          analyser[key] = [str(item) if isinstance(item, ObjectId) else item for item in value]
        elif isinstance(value, dict) and key != 'versions':  # Skip versions as we already handled it
          # Recursively convert ObjectIds in nested dicts
          for nested_key, nested_value in value.items():
            if isinstance(nested_value, ObjectId):
              value[nested_key] = str(nested_value)
            elif isinstance(nested_value, list):
              value[nested_key] = [str(item) if isinstance(item, ObjectId) else item for item in nested_value]
        
      return analyser
  
    except Exception as e:
      print(f"Error in Analyser.get for id {analyser_id}: {e}")
      print(traceback.format_exc())
      raise e

  def autoSelectSamples(dataset_id, items, labels, example_refs, start_index, end_index, num_predictions, analyser_type):
            
      if dataset_id == None:# Testing analyser

        labelled_to_unlabelled_ratio = 0.95
        example_to_nonexample_ratio = 0.2
        target_num_labelled = int(round(labelled_to_unlabelled_ratio * int(num_predictions),None))
        target_num_examples = int(round(example_to_nonexample_ratio * target_num_labelled,None))
        target_num_labelled_non_example = target_num_labelled - target_num_examples
        target_num_unlabelled = int(num_predictions) - target_num_examples - target_num_labelled_non_example

        example_items = []
        labelled_items = []
        unlabelled_items = []

        if (analyser_type == "binary"):
          pos_to_neg_ratio=0.5
          target_pos_labelled_items = int(round(target_num_labelled_non_example*pos_to_neg_ratio,None))
          target_neg_labelled_items = target_num_labelled_non_example - target_pos_labelled_items
          pos_labelled_items = []
          neg_labelled_items = []

        for i,item in enumerate(items):

          label_res = [label for label in labels if str(label['item_id']) == str(item["_id"])]
          item['index'] = i
          item['label'] = label_res[0]['value'] if (len(label_res)>0) else ""
          item['example'] = True if item['_id'] in example_refs else False

          if item['example']:
            example_items.append(item)
          elif item['label'] != "":
            labelled_items.append(item)
            if (analyser_type == "binary"):
              if str(item['label'])=="0":
                neg_labelled_items.append(item)
              elif str(item['label'])=="1":
                pos_labelled_items.append(item)
          else:
            unlabelled_items.append(item)

        # Checking this on the front end, this is a back-up
        if (analyser_type == "binary") and len(pos_labelled_items)==0:
          raise Exception("Please exclude at least one positively labelled item from your selected examples.")

        if len(unlabelled_items)<target_num_unlabelled:
          diff = target_num_unlabelled - int(len(labelled_items))
          labelled_split_diff = round(diff * (labelled_to_unlabelled_ratio * (1-example_to_nonexample_ratio)),None)
          target_num_labelled_non_example = target_num_labelled_non_example + labelled_split_diff
          target_num_example = target_num_example + (diff - labelled_split_diff)
          target_num_unlabelled = target_num_unlabelled - diff

        if len(example_items)<target_num_examples:
          diff = target_num_examples - int(len(example_items))
          target_num_labelled_non_example = target_num_labelled_non_example + diff
          target_num_examples = target_num_examples - diff

        if len(labelled_items)<target_num_labelled_non_example:
          diff = target_num_labelled_non_example - int(len(labelled_items))
          target_num_labelled_non_example = len(labelled_items)
          target_num_unlabelled = (target_num_unlabelled + diff) if (target_num_unlabelled + diff) < len(unlabelled_items) else len(unlabelled_items)


        #Balancing to make sure positive, labelled non-examples are included
        if (analyser_type == "binary"):
          if len(pos_labelled_items)<target_pos_labelled_items:
            target_pos_labelled_items = len(pos_labelled_items)
            target_neg_labelled_items = target_num_labelled_non_example - target_pos_labelled_items
          if len(neg_labelled_items)<target_neg_labelled_items:
            target_neg_labelled_items = len(neg_labelled_items)
            target_pos_labelled_items = target_num_labelled_non_example - target_neg_labelled_items

        random_example_item_indicies = random.sample(range(0,len(example_items)),target_num_examples)
        random_unlabelled_item_indicies = random.sample(range(0,len(unlabelled_items)),target_num_unlabelled)

        random_example_items = [item['index'] for i, item in enumerate(example_items) if i in random_example_item_indicies]
        random_unlabelled_items = [item['index'] for i, item in enumerate(unlabelled_items) if i in random_unlabelled_item_indicies]

        if (analyser_type == "binary"):
          random_pos_labelled_item_indicies = random.sample(range(0,len(labelled_items)),target_pos_labelled_items)
          random_pos_labelled_items = [item['index'] for i, item in enumerate(labelled_items) if i in random_pos_labelled_item_indicies]
          random_neg_labelled_item_indicies = random.sample(range(0,len(labelled_items)),target_neg_labelled_items)
          random_neg_labelled_items = [item['index'] for i, item in enumerate(labelled_items) if i in random_neg_labelled_item_indicies]
          item_indices = [*random_example_items,*random_pos_labelled_items,*random_neg_labelled_items,*random_unlabelled_items]
        else:
          random_labelled_item_indicies = random.sample(range(0,len(labelled_items)),target_num_labelled_non_example)
          random_labelled_items = [item['index'] for i, item in enumerate(labelled_items) if i in random_labelled_item_indicies]
          item_indices = [*random_example_items,*random_labelled_items,*random_unlabelled_items]
        
        item_indices.sort()

      else:
        item_indices=random.sample(range(start_index,end_index),num_predictions)

      sample_ids = [x['_id'] for index, x in enumerate(items) if index in item_indices]

      return sample_ids

  def autoSelectExamples(labelled_items, start_index, end_index, num, analyser_type):

    if analyser_type == "binary":

      # Select balanced sample from dataset.artworks that has labels
      item_subset = [item for index, item in enumerate(labelled_items) if int(index)>=int(start_index) and int(index)<=int(end_index) ]
      
      positive_items = [item for item in item_subset if item['_textLabel']['value'] == 1]
      negative_items = [item for item in item_subset if item['_textLabel']['value'] == 0]

      target_positive = int(round(num*0.5,None))
      target_negative = num - target_positive

      if len(positive_items)<target_positive:
        diff = target_positive - int(len(positive_items))
        raise Exception("Autoselect Failed: Please provide " + str(diff) + " more positive items.")

      if len(negative_items)<target_negative:
        diff = target_negative - int(len(negative_items))
        raise Exception("Autoselect Failed: Please provide " + str(diff) + " more negative items.")
      
      chosen_positive_examples = random.sample(positive_items,target_positive)
      chosen_negative_examples = random.sample(negative_items,target_negative)

      chosen_examples = [*chosen_positive_examples,*chosen_negative_examples]
      chosen_example_ids = [str(item['_id']) for item in chosen_examples]

    elif analyser_type == "score":

      # For score models, use binary labels (positive/negative) for training examples
      # Select balanced sample from dataset.artworks that has labels
      item_subset = [item for index, item in enumerate(labelled_items) if int(index)>=int(start_index) and int(index)<=int(end_index) ]
      
      positive_items = [item for item in item_subset if item['_textLabel']['value'] == 1]
      negative_items = [item for item in item_subset if item['_textLabel']['value'] == 0]

      target_positive = int(round(num*0.5,None))
      target_negative = num - target_positive

      if len(positive_items)<target_positive:
        diff = target_positive - int(len(positive_items))
        raise Exception("Autoselect Failed: Please provide " + str(diff) + " more positive items.")

      if len(negative_items)<target_negative:
        diff = target_negative - int(len(negative_items))
        raise Exception("Autoselect Failed: Please provide " + str(diff) + " more negative items.")
      
      chosen_positive_examples = random.sample(positive_items,target_positive)
      chosen_negative_examples = random.sample(negative_items,target_negative)

      chosen_examples = [*chosen_positive_examples,*chosen_negative_examples]
      chosen_example_ids = [str(item['_id']) for item in chosen_examples]

    else:

      # Select random sample from dataset.artworks that has labels
      item_subset = [item for index, item in enumerate(labelled_items) if int(index)>=int(start_index) and int(index)<=int(end_index) ]
      chosen_examples = random.sample(item_subset,num)
      chosen_example_ids = [str(item['_id']) for item in chosen_examples]

    return chosen_examples, chosen_example_ids

  

  
  def createLLMprompt(
      analyser_type, 
      analyser_format,
      task_description, 
      labelling_guide, 
      dataset_id, 
      labelset_id, 
      include_examples=False,
      auto_select_examples=None,
      example_ids=None,
      num_examples=None,
      examples_start_index=None,
      examples_end_index=None
  ):

    try:
      
      prompt_intro = 'You are an expert art historian and critic, able to identify key attributes about any piece of artwork.\n'
      prompt_format = ""
      prompt_task = task_description + "\n"
      prompt_guidance = labelling_guide + "\n"
      prompt_examples = ""
      prompt_end=""
      data_format = "a " + analyser_format + " sample" if analyser_format != "textimage" else "an item (containing an image and a piece of text)"
      input_label = analyser_format.upper() + ": " #TODO Fix this for textimage

      # Setup format guidance based on analyser type
      if analyser_type == 'binary':
        prompt_format_0 = "When given "
        prompt_format_1 = """, you are able to classify it as either 'positive' or 'negative'.
'positive' means that it matches the trend we are looking for, 'negative' means that it doesn't.\n\n
Data format:\nINPUT:\n"""
        prompt_format_2 = """ to be analysed\n\nOUTPUT:\nRESULT:'positive' or 'negative'\nREASON:(Optional) Explanation of the result\n\n"""
        prompt_format = "".join([prompt_format_0,data_format,prompt_format_1,input_label,data_format,prompt_format_2])

      if analyser_type == 'score':
        prompt_format_0 = "When given "
        prompt_format_1 = """, you are able to grade it on a scale of 0-5.\n\n
Data format:\nINPUT:\n"""
        prompt_format_2 = """ to be analysed\n\nOUTPUT:\nRESULT:only one number: 0, 1, 2, 3, 4, or 5\nREASON:(Optional) Explanation of the result\n\n"""
        prompt_format = "".join([prompt_format_0,input_label,data_format,prompt_format_1,data_format,prompt_format_2])

      if analyser_type == 'opinion':
        prompt_format_0 = "When given "
        prompt_format_1 = """, you are able to provide your expert opinion about it.\n\n
Data format:\nINPUT:\n"""
        prompt_format_2 = """ to be analysed\n\nOUTPUT:\nRESULT:Your detailed opinion in 2-3 sentences\nREASON:(Optional) Additional explanation or context\n\n"""
        prompt_format = "".join([prompt_format_0,data_format,prompt_format_1,input_label,data_format,prompt_format_2])

      # Get examples

      labelled_items = []
      unlabelled_items = []

      if dataset_id != None and len(str(dataset_id)) > 0:

        dataset = Dataset.get(dataset_id, True, True)

        if labelset_id != None and len(str(labelset_id)) > 0:
          labelset = Labelset.get(None,labelset_id, True)
          
          for item in dataset['artworks']:
            newItem = item.copy()
            newItem['_textLabel'] = {}
            for label in labelset['labels']:
              # Convert both to strings for comparison to avoid ObjectId issues
              if str(label["item_id"]) == str(item["_id"]):
                newItem['_textLabel'] = label
                labelled_items.append(newItem)
                break
            else:
              # Item not found in labelset, add to unlabelled items
              unlabelled_items.append(newItem)
          
      if auto_select_examples=="true":          
          start_index= int(examples_start_index) if examples_start_index != None else 0
          end_index= int(examples_end_index) if examples_end_index != None else int(len(labelled_items))
          num = int(num_examples) if num_examples != None else 5
          chosen_examples, chosen_example_ids = Analyser.autoSelectExamples(labelled_items, start_index, end_index, num, analyser_type)
      
      else:

        if example_ids!=None:

          chosen_example_ids = example_ids
          chosen_examples = []
          
          # First try to find examples in labelled items
          for item in labelled_items:
            if str(item['_id']) in example_ids:
              chosen_examples.append(item)
          
          # If we don't have enough examples, add unlabelled items
          remaining_ids = [id for id in example_ids if id not in [str(item['_id']) for item in chosen_examples]]
          
          for item in unlabelled_items:
            if str(item['_id']) in remaining_ids:
              # Create a dummy label for unlabelled items
              if analyser_type == 'binary':
                item['_textLabel'] = {
                  'value': 1,  # Default positive for binary
                  'rationale': 'Example provided for training'
                }
              elif analyser_type == 'score':
                item['_textLabel'] = {
                  'value': 3,  # Middle score for score
                  'rationale': 'Example provided for training'
                }
              elif analyser_type == 'opinion':
                item['_textLabel'] = {
                  'value': 1,  # Default positive for opinion training examples
                  'rationale': 'This is a good example of the pattern we are looking for.'
                }
              chosen_examples.append(item)

        else:
          # If no examples are provided and we don't want to include examples, that's fine
          if not include_examples:
            chosen_examples = []
            chosen_example_ids = []
          else:
            raise Exception("Error: Please provide examples.")

      if include_examples and (len(chosen_examples) > 0):
        
        if analyser_format == "text":

          str_template = input_label[:-2] + "-{0}:{1}\nRESULT-{2}:{3}{4}\n"

          if analyser_type == 'binary': 
            examples = [str_template.format(
              str(i),
              next((x for x in item["content"] if x['content_type'] == 'text'))['content_value']["text"],
              str(i), 
              'positive' if item['_textLabel']['value'] == 1 else 'negative',
              ("" if (len(item['_textLabel']['rationale']) == 0) else "\nREASON:" + item['_textLabel']['rationale'])
            ) for i, item in enumerate(chosen_examples)]

          if analyser_type == 'score': 
            examples = [str_template.format(
              str(i),
              next((x for x in item["content"] if x['content_type'] == 'text'))['content_value']["text"],
              str(i),
              'positive' if item['_textLabel']['value'] == 1 else 'negative',
              ("" if (len(item['_textLabel']['rationale']) == 0) else "\nREASON:" + item['_textLabel']['rationale'])
            ) for i, item in enumerate(chosen_examples)]

          if analyser_type == 'opinion': 
            examples = [str_template.format(
              str(i),
              next((x for x in item["content"] if x['content_type'] == 'text'))['content_value']["text"],
              str(i),
              # For opinion models, use rationale as the opinion text, or generate a default opinion based on binary value
              item['_textLabel']['rationale'] if item['_textLabel']['rationale'] else 
              ('This is a good example of the pattern we are looking for.' if item['_textLabel']['value'] == 1 else 
               'This is not a good example of the pattern we are looking for.'),
              ("" if (len(item['_textLabel']['rationale']) == 0) else "\nREASON:" + item['_textLabel']['rationale'])
            ) for i, item in enumerate(chosen_examples)]

          prompt_examples = "-----\n\nExamples:\n\n" + "\n".join(examples) + "-----\n\n"

          prompt = "".join([prompt_intro,prompt_format,prompt_task,prompt_guidance,prompt_examples,prompt_end])
          
        elif analyser_format == "image" or analyser_format == "textimage" :
          # For image format, we need to include examples in the formatted_examples
          # but the actual prompt will be handled by the LLM providers
          # The examples are stored in formatted_examples for later use
          prompt = "".join([prompt_intro,prompt_format,prompt_task,prompt_guidance])
          
          # Add examples section to the prompt for image format
          if len(chosen_examples) > 0:
            prompt += "\n-----\n\nExamples:\n\n"
            for i, item in enumerate(chosen_examples):
              if analyser_format == "textimage":
                # For textimage, include both text and image
                text_content = next((x for x in item["content"] if x['content_type'] == 'text'), None)
                if text_content:
                  prompt += f"TEXT-{i}:{text_content['content_value']['text']}\n"
                prompt += f"IMAGE-{i}:[image data]\n"
              else:
                # For image only
                prompt += f"IMAGE-{i}:[image data]\n"
              
              # Add the result
              if analyser_type == 'binary':
                result = 'positive' if item['_textLabel']['value'] == 1 else 'negative'
              elif analyser_type == 'score':
                result = str(item['_textLabel']['value'])
              elif analyser_type == 'opinion':
                result = item['_textLabel']['rationale'] if item['_textLabel']['rationale'] else 'This is a good example of the pattern we are looking for.'
              
              prompt += f"RESULT-{i}:{result}\n"
              
              # Add rationale if available
              if item['_textLabel']['rationale']:
                prompt += f"REASON:{item['_textLabel']['rationale']}\n"
              
              prompt += "\n"
            
            prompt += "-----\n\n"

      else:

        prompt_examples = ""
        prompt = "".join([prompt_intro,prompt_format,prompt_task,prompt_guidance,prompt_end])

      formatted_examples = []
      for ex in chosen_examples:
        example = {
          "_id":str(ex["_id"]),
          "label":ex['_textLabel']['value'],
          "rationale":ex['_textLabel']['rationale']
        }
        if analyser_format == "text":
          example['text'] = next((x for x in ex["content"] if x['content_type'] == 'text'))['content_value']["text"]
        elif analyser_format == "image" or analyser_format == "textimage":
          # For image formats, include image data
          image_content = next((x for x in ex["content"] if x['content_type'] == 'image'), None)
          if image_content:
            example['image'] = image_content['content_value']['image_storage_id']
          if analyser_format == "textimage":
            # For textimage, also include text
            text_content = next((x for x in ex["content"] if x['content_type'] == 'text'), None)
            if text_content:
              example['text'] = text_content['content_value']['text']
        formatted_examples.append(example)


      return prompt, formatted_examples, chosen_example_ids

    except Exception as e:
      print("exception in createLLMprompt()")
      print(e)
      raise e





  def all(user_id=None,includeNames=True,includeVersions=False):

    try:
      public_classifiers = analyser_collection.find({ "owner" : { "$exists" : False } }) # TODO change this to a system based on visibility
      private_classifiers = analyser_collection.find({ "$or":[ {  "owner" : user_id }, { "users" : { "$in" : [user_id] } }]})

      classifiers_list = []
      for classifier in list(private_classifiers):
        try:
          classifier_data = Analyser.get(classifier['_id'],includeNames,includeVersions)
          classifiers_list.append(classifier_data)
        except Exception as e:
          print(f"Error getting analyser {classifier.get('_id', 'unknown')}: {e}")
          # Continue with next analyser instead of failing completely
          continue

      for classifier in list(public_classifiers):
        try:
          classifier_data = Analyser.get(classifier['_id'],includeNames,includeVersions)
          classifiers_list.append(classifier_data)
        except Exception as e:
          print(f"Error getting analyser {classifier.get('_id', 'unknown')}: {e}")
          # Continue with next analyser instead of failing completely
          continue

      return classifiers_list
    except Exception as e:
      print(f"Error in Analyser.all: {e}")
      print(traceback.format_exc())
      raise e
  

  def use(analyser_id,sample_ids, num_predictions, auto_select_sample, dataset_id=None, start_index=None, end_index=None):

    try:

      analyser = Analyser.get(analyser_id,False,False)
      dataset_id_ref = ObjectId(analyser['dataset_id']) if dataset_id==None else ObjectId(dataset_id)
      labelset_id_ref = ObjectId(analyser['labelset_id']) # Only using labelset for testing
      dataset = Dataset.get(dataset_id_ref,True,True)
      labelset = Labelset.get(None, labelset_id_ref, True) 

      example_refs = analyser['example_refs']
      analyser_type = analyser['analyser_type']
      analyser_format = analyser['analyser_format']
      item_range = dataset['artworks']

      if auto_select_sample == 'true':

        start_index = start_index if start_index!=None else 0
        end_index = end_index if end_index!=None else len(item_range)
        num_predictions = num_predictions if num_predictions<1000 else 1000

        sample_ids = Analyser.autoSelectSamples(dataset_id,dataset['artworks'],labelset['labels'],example_refs,start_index,end_index,num_predictions,analyser_type)

      # Get positions of the chosen sample items
      item_indices = []
      for id in sample_ids:
        item_index = [index for index, x in enumerate(item_range) if x['_id'] == id]
        if (len(item_index)>0):
          item_indices.append(item_index[0])
      item_indices.sort()

      if (analyser_format == "image") or (analyser_format == "textimage"):
        # Get Embeddings for examples
        for ex in analyser["examples"]:
          item = Item.get(ex["_id"])
          full_item = Item.getFullItem(item,True)
          base64embeddings = [e['value'] for e in full_item["content"][0]["content_value"]["embeddings"] if e['format']=="base64"]
          if len(base64embeddings) > 0:
            ex['image'] = base64embeddings[0]
          
          # Get text for textimage
          if (analyser_format == "textimage"):
            text = [e['content_value']['text'] for e in full_item["content"] if e['content_type']=='text']
            ex['text'] = text[0]

      prediction_results = llm.use_model(analyser['prompt'],analyser['examples'],item_indices,item_range, analyser)

      indexed_preds = []
      batch_success_count = 0
      batch_filtered_success_count = 0
      error_objs = []

      for batch in prediction_results:
        if (batch['status']=="success") or (batch['status']=="filtered_success"):
          if (batch['status']=="success"):
            batch_success_count = batch_success_count + 1
          #if content filter gets triggered
          elif (batch['status']=="filtered_success"):
            batch_filtered_success_count = batch_filtered_success_count + 1
            #get error messages containing content themes to be displayed in frontend
            for e in batch['error']: 
               print(e)
               error_objs.append({
                "batch_num":batch['batch_num'],
                "error": e
              })
          for i, pred in enumerate(batch['results']):
            index = batch['batch_indicies'][i]
            item = item_range[index]
            indexed_preds.append({str(item['_id']):pred})
        else:
          error_objs.append({
            "batch_num":batch['batch_num'],
            "error":batch['error']['error']
          })
      
      if (batch_success_count > 0) or (batch_filtered_success_count > 0):
        if dataset_id == None and len(indexed_preds) != len(error_objs): # Testing analyser
          try:
            accuracy, unlabelled_test_data = llm.compute_accuracy(labelset['labels'],dataset['artworks'],example_refs,indexed_preds,analyser_type,analyser["analyser_format"], False)
          except Exception as e:
            print(f"Accuracy calculation failed: {e}")
            accuracy, unlabelled_test_data = "0.0", []
        else:
          accuracy, unlabelled_test_data = "", []

        if dataset_id == None:
          Analyser.update(analyser_id,{
            "sample_ids":sample_ids,
            "predictions":indexed_preds,
            "accuracy":accuracy
          },None,False)

        status = "success"

        if dataset_id == None: #testing only
          results_obj = {
            "status": status,
            "predictions": indexed_preds,
            "unlabelled_test_data": unlabelled_test_data
          }

        else: #use tab
          results_obj = {
            "status": status,
            "predictions": indexed_preds
          }

        if (len(error_objs)>0):
          results_obj['status'] = "partial_success"
          results_obj["errors"] = error_objs

        if(batch_filtered_success_count > 0):
          results_obj['status'] = "filtered_success"

        return results_obj
      
      else:
        if len(error_objs)>0:
          print(error_objs)
          if next((i for i in error_objs if "Runtime error" in i["error"]), False):
            return "Runtime error: Your device is out of memory."
        raise Exception("Error: No prediction results. Please contact the technical team.")
    
    except Exception as e:
      print(e)

  
  def getAccuracy(analyser_id):

    try:

      analyser = Analyser.get(analyser_id, False, True)
      analyser_type = analyser['analyser_type']
      
      labelset=Labelset.get(None, analyser["labelset_id"],True)
      dataset=Dataset.get(analyser["dataset_id"],True)

      current_version = [v for v in analyser['versions'] if (v is not None) and (v['id'] == analyser['version'])]
      
      if not current_version:
        raise Exception(f"No version found for analyser {analyser_id} with version {analyser['version']}")
      
      version_data = current_version[0]      
      trained_example_indices = version_data.get('example_refs', [])
      
      if 'predictions' not in version_data:
        predictions = analyser.get('predictions', [])
        if not predictions:
          raise Exception("No predictions available. Please run predictions on test samples before computing accuracy.")
      else:
        predictions = version_data['predictions']

      if not predictions or len(predictions) == 0:
        raise Exception("No test samples available. Please select test samples and run predictions before computing accuracy.")

      accuracy_result = llm.compute_accuracy(labelset['labels'],dataset['artworks'],trained_example_indices,predictions,analyser_type,analyser["analyser_type"],False)
      
      if accuracy_result and len(accuracy_result) == 2:
        metrics, unlabelled_test_data = accuracy_result
        
        if isinstance(metrics, dict):
          primary_accuracy = metrics.get('accuracy', metrics.get('exact_accuracy', '0.0'))
        else:
          primary_accuracy = metrics
          metrics = {"accuracy": primary_accuracy}
        
        return metrics, unlabelled_test_data
      else:
        raise Exception("Accuracy computation failed - no valid result returned")

    except Exception as e:
      print(e)
      raise e


  def delete(analyser_id):
    analyser_collection.delete_one({"_id": ObjectId(analyser_id)})

  def update(analyser_id, data, config, is_new_version=False):

    try:

      auto_select_examples = config['auto_select_examples'] if config!=None else None
      num_examples = config['num_examples'] if config!=None else None
      examples_start_index = config['examples_start_index'] if config!=None else None
      examples_end_index = config['examples_end_index'] if config!=None else None

      id = analyser_id if isinstance(analyser_id,ObjectId) else ObjectId(analyser_id)

      analyser = Analyser.get(analyser_id,False,True)

      new_name = data['name'] if 'name' in data else analyser['name']
      new_analyser_type = data['analyser_type'] if 'analyser_type' in data else analyser['analyser_type']
      new_analyser_format = data['analyser_format'] if 'analyser_format' in data else (analyser['analyser_format'] if 'analyser_format' in analyser else "")
      new_category_id = data['category_id'] if 'category_id' in data else analyser['category_id']
      new_task_description = data['task_description'] if 'task_description' in data else analyser['task_description']
      new_labelling_guide = data['labelling_guide'] if 'labelling_guide' in data else analyser['labelling_guide']
      new_dataset_id = data['dataset_id'] if 'dataset_id' in data else analyser['dataset_id']
      new_labelset_version = ""
      new_labelset_id = data['labelset_id'] if ('labelset_id' in data) else analyser['labelset_id']
      new_example_refs = data['example_refs'] if ('example_refs' in data) else analyser['example_refs']
      new_prompt_examples = data['examples'] if ('examples' in data) else (analyser['examples'] if 'examples' in analyser else [])
      new_preds = data['predictions'] if ('predictions' in data) else (analyser['predictions'] if 'predictions' in analyser else [])
      new_accuracy = float(data['accuracy']) if ('accuracy' in data) and data['accuracy'] != None and len(str(data['accuracy']))>0 else (analyser['accuracy'] if 'accuracy' in analyser else "")
      new_sample_ids = data['sample_ids'] if ('sample_ids' in data) else (analyser['sample_ids'] if 'sample_ids' in analyser else "")

      if (('analyser_type' in data) or 
          ('task_description' in data) or 
          ('labelling_guide' in data) or
          ('dataset_id' in data) or
          ('labelset_id' in data) or
          ('example_refs' in data) or 
          (auto_select_examples!=None and auto_select_examples)):
        new_prompt, new_prompt_examples, new_example_refs = Analyser.createLLMprompt(
          new_analyser_type,
          new_analyser_format,
          new_task_description,
          new_labelling_guide,
          new_dataset_id,
          new_labelset_id,
          formatExamplesInsidePrompt,
          auto_select_examples,
          new_example_refs,
          num_examples,
          examples_start_index,
          examples_end_index
        )
      else:
        new_prompt = analyser['prompt']

      if len(analyser['labelset_id'])>0:
        labelset = Labelset.get(None,analyser['labelset_id'])
        new_labelset_version = data['labelset_version'] if 'labelset_version' in data else labelset['version']

      for e in new_prompt_examples:
        if "image" in e:
          e['image'] = "<Embedding Removed>"

      new_data_obj = {
        "name":new_name,
        "analyser_type":new_analyser_type,
        "analyser_format":new_analyser_format,
        "category_id":new_category_id,
        "task_description":new_task_description,
        "labelling_guide":new_labelling_guide,
        "dataset_id":new_dataset_id,
        "labelset_id":new_labelset_id,
        "labelset_version": new_labelset_version,
        "example_refs": new_example_refs,
        "examples":new_prompt_examples,
        "prompt": new_prompt,
        "predictions": new_preds if not is_new_version else [],
        "accuracy": new_accuracy if not is_new_version else "",
        "sample_ids": new_sample_ids,
        "last_updated" : datetime.datetime.now()
      }

      update_ref = {
        "_id": id
      }

      analyser_collection.update_one(update_ref,{
        "$set":new_data_obj
      })

      labelset_update_data = {"analyser_id":analyser_id}

      update_keys = list(data.keys())

      if ('labelling_guide' in update_keys):
        labelset_update_data['labelling_guide'] = data['labelling_guide']

      if is_new_version:
  
        labelset = Labelset.get(None,new_labelset_id)

        new_version_number = str(int(max(int(v['id']) for v in analyser['versions'] if v!=None)) + 1)

        new_data_obj["id"] = new_version_number 
        new_data_obj['labelset_version'] = labelset['version']

        new_data_obj['predictions'] = []
        new_data_obj['accuracy'] = ""

        analyser_collection.update_one(update_ref,{
          "$push":{
            "versions":new_data_obj
          }
        })

        analyser_collection.update_one(update_ref,{
          "$set":{
            "version":new_version_number,
            "labelset_version":labelset['version']
          }
        })

        labelset_version = str(int(max(int(v['id']) for v in labelset['versions'] if v!=None)) + 1)

        labelset_update_data['labelset_version'] = labelset_version

        Labelset.update(new_labelset_id, labelset_update_data, True)

        if len(analyser['versions']) > 25:
          non_keep_versions = [v for v in analyser['versions'] if (v != None) and ((("keep" in v) and (v['keep'] == "false")) or ("keep" not in v))]
          if len(non_keep_versions) == 0:
            raise Exception("Cannot remove old versions as all are marked for keeps.")
          else:
            last_version = non_keep_versions[0]['id']
            analyser_collection.update_one(update_ref,
              {
                "$pull":{"versions":{"id":last_version}}
              }
            )

        if any(x['id'] == 0 for x in analyser['versions']):
          analyser_collection.update_one(update_ref,
            {
              "$pull":{"versions":{"id":0}}
            }
          )

      else:

        update_ref = {
          "_id": id,
          "versions.id":str(int(analyser['version']))
        }

        if 'predictions' in data:
          analyser_collection.update_one(update_ref,{
            "$set":{"versions.$.predictions":data['predictions']}
          })

        if 'accuracy' in data:
          analyser_collection.update_one(update_ref,{
            "$set":{"versions.$.accuracy":data['accuracy']}
          })

        if 'example_refs' in data:
          analyser_collection.update_one(update_ref,{
            "$set":{"versions.$.example_refs":data['example_refs']}
          })

        if 'examples' in data:
          analyser_collection.update_one(update_ref,{
            "$set":{"versions.$.examples":data['examples']}
          })
        
        if 'task_description' in data:
          analyser_collection.update_one(update_ref,{
            "$set":{"versions.$.task_description":data['task_description']}
          })

        if 'labelling_guide' in data:
          analyser_collection.update_one(update_ref,{
            "$set":{"versions.$.labelling_guide":data['labelling_guide']}
          })

        if 'sample_ids' in data:
          analyser_collection.update_one(update_ref,{
            "$set":{"versions.$.sample_ids":data['sample_ids']}
          })

        if 'prompt' in data:
          analyser_collection.update_one(update_ref,{
            "$set":{"versions.$.prompt":data['prompt']}
          })

        if 'category_id' in data:
          analyser_collection.update_one(update_ref,{
            "$set":{"versions.$.category_id":data['category_id']}
          })

    except Exception as e:
      print(e)

  def update_version(analyser_id, version_id):

    try:

      analyser = Analyser.get(analyser_id,False,True)
      versions = analyser["versions"]

      version = [v for v in versions if (v!=None) and str(v['id'])==str(version_id)]

      update_ref = {
        "_id": ObjectId(analyser_id)
      }

      analyser_collection.update_one(update_ref,{
        "$set":{
          "version":str(version_id)
        }
      })

      Analyser.update(analyser_id,version[0],None,False)

      Labelset.change_version(version[0]['labelset_id'],version[0]['labelset_version'])
    
    except Exception as e:
      print(e)

  def update_version_details(analyser_id, version_id, version_data):

    try:

      analyser = Analyser.get(analyser_id,False,True)
      versions = analyser["versions"]

      version = [v for v in versions if (v!=None) and str(v['id'])==str(version_id)]

      update_ref = {
        "_id": ObjectId(analyser_id),
        "versions.id": version_id 
      }

      if ('keep' in version_data):
        analyser_collection.update_one(update_ref,{
          "$set":{"versions.$.keep":version_data['keep']}
        })

      if ('version_name' in version_data):
        analyser_collection.update_one(update_ref,{
          "$set":{"versions.$.version_name":version_data['version_name']}
        })

    except Exception as e:
      print(e)

  def change_model(new_model_name, model_type, new_model_source):
    try:
      llm.set_model(new_model_name, model_type, new_model_source)
    except Exception as e:
      print(e)
  
  def get_model(model_type):
    try:
      return llm.get_model(model_type)
    except Exception as e:
      print(e)


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

  def update_text_subcontent(item_id, subcontent_value):

    subcontent_value = json.loads(subcontent_value)

    subcontent = {
      "subcontent_value":subcontent_value
    }

    query = { '_id': ObjectId(item_id) }
    newvalue = { "$set": { 'content.$[].subcontent': subcontent } }
    item_collection.update_one(query, newvalue, upsert=True)

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


class Resultset():

  def create(owner_id,analyser_id,dataset_id,labelset_id,results):
     
    results_obj = {
      "owner":owner_id,
      "analyser_id":analyser_id,
      "dataset_id": dataset_id,
      "labelset_id": labelset_id,
      "results":results
    }

    resultset_id = resultset_collection.insert_one(results_obj).inserted_id

    return resultset_id
  
  def get(resultset_id):
    resultset_db_res = resultset_collection.find({"_id":ObjectId(resultset_id)})
    resultset = list(resultset_db_res)[0]
    return resultset

  def get_all(dataset_id=None,analyser_id=None,labelset_id=None):
    try:
      if dataset_id != None:
        ref = {"dataset_id":dataset_id}
      elif analyser_id != None:
        ref = {"analyser_id":analyser_id}
      elif labelset_id != None:
        ref = {"labelset_id":labelset_id}
      else:
        ref = {}

      resultsets_db_res = labelset_collection.find(ref)
      resultsets = list(resultsets_db_res)

      for resultset in resultsets:
        resultset["_id"] = str(resultset["_id"])
        resultset["analyser_id"] = str(resultset["analyser_id"])
        resultset["dataset_id"] = str(resultset["dataset_id"])
        resultset["labelset_id"] = str(resultset["labelset_id"])

    except Exception as e:
      print(e)
      
    return resultsets

  def get(dataset_id=None, analyser_id=None, labelset_id=None, resultset_id=None):
    try:
      if resultset_id!= None:
        resultset_id = resultset_id if isinstance(resultset_id,ObjectId) else ObjectId(resultset_id)
        resultset_db_res = resultset_collection.find({"_id":resultset_id})
      elif analyser_id!= None:
        resultset_db_res = labelset_collection.find({"analyser_id":analyser_id})
      elif dataset_id!= None:
        resultset_db_res = labelset_collection.find({"dataset_id":dataset_id})
      elif labelset_id!= None:
        resultset_db_res = labelset_collection.find({"labelset_id":labelset_id})
      resultset_res = list(resultset_db_res)
      resultset = resultset_res[0]

      return resultset

    except Exception as e:
      print(e)
      raise e
    



user_collection = db["user"]

class User():
    @staticmethod
    def create_local_user(username, email, password):
        """Create a new local user with username, email, and hashed password"""
        from werkzeug.security import generate_password_hash
        import uuid
        
        # Check if username or email already exists
        if user_collection.find_one({"$or": [{"username": username}, {"email": email}]}):
            return None, "Username or email already exists"
        
        # Generate unique user_id (local format: local_<uuid>)
        user_id = f"local_{uuid.uuid4().hex}"
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        london_tz = pytz.timezone('Europe/London')
        current_time = datetime.datetime.now(london_tz)
        
        user_obj = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "first_connection": current_time,
            "last_connection": current_time,
            "previous_connection": None,
            "last_event_type": "register",
            "last_event_time": current_time,
            "role": "",
            "affiliation": ""
        }
        
        user_collection.insert_one(user_obj)
        return user_id, None
    
    @staticmethod
    def verify_password(user_id, password):
        """Verify password for a user"""
        from werkzeug.security import check_password_hash
        user = user_collection.find_one({"user_id": user_id})
        if user and "password_hash" in user:
            return check_password_hash(user["password_hash"], password)
        return False
    
    @staticmethod
    def authenticate_local_user(username_or_email, password):
        """Authenticate user by username/email and password. Returns user_id if successful."""
        from werkzeug.security import check_password_hash
        user = user_collection.find_one({
            "$or": [{"username": username_or_email}, {"email": username_or_email}]
        })
        if user and "password_hash" in user:
            if check_password_hash(user["password_hash"], password):
                return user.get("user_id"), user.get("username"), user.get("email")
        return None, None, None
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user data by user_id"""
        user = user_collection.find_one({"user_id": user_id})
        if user:
            # Remove password hash from returned data
            user_data = dict(user)
            user_data.pop("password_hash", None)
            return user_data
        return None
    
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
        """Get user preferences including text provider"""
        user = user_collection.find_one({"user_id": user_id})
        if user:
            preferences = user.get("preferences", {})
            # Default to "ollama" if not set
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
            if text_provider not in ["ollama", "openai"]:
                return False, "Invalid text provider. Must be 'ollama' or 'openai'"
            preferences["text_provider"] = text_provider
        
        update_data = {"preferences": preferences}
        user_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data},
            upsert=True
        )
        return True, "Preferences updated successfully"



class AnalysisHistory():
    def create(user_id, analyser_id, dataset_id, selected_items, chat_messages, analysis_summary):
        """Create a new analysis history record"""
        london_tz = pytz.timezone('Europe/London')
        current_time = datetime.datetime.now(london_tz)
        
        analysis_obj = {
            "user_id": user_id,
            "analyser_id": analyser_id,
            "dataset_id": dataset_id,
            "selected_items": selected_items,
            "selected_items_count": len(selected_items),
            "chat_messages": chat_messages,
            "analysis_summary": analysis_summary,
            "created_at": current_time,
            "status": "completed"
        }
        
        analysis_id = analysis_history_collection.insert_one(analysis_obj).inserted_id
        return str(analysis_id)
    
    def get_all(user_id):
        """Get all analysis history for a user"""
        try:
            analyses = list(analysis_history_collection.find({"user_id": user_id}).sort("created_at", -1))
            
            for analysis in analyses:
                analysis["_id"] = str(analysis["_id"])
                analysis["analyser_id"] = str(analysis["analyser_id"])
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
                analysis["analyser_id"] = str(analysis["analyser_id"])
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




