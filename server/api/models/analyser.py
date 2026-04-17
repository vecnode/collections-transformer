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


