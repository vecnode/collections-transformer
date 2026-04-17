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


