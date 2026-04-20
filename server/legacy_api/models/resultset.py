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

