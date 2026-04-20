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





