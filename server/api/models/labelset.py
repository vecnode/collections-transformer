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
    

