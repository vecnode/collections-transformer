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



