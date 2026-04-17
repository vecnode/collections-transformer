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


