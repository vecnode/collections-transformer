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
                

