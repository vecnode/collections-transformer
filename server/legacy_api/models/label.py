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


