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



