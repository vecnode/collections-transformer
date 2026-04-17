@endpoints_bp.route('/backend/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({
                "status": "400",
                "error": "Username, email, and password are required"
            }), 400
        
        if len(password) < 6:
            return jsonify({
                "status": "400",
                "error": "Password must be at least 6 characters"
            }), 400
        
        user_id, error = models.User.create_local_user(username, email, password)
        if error:
            return jsonify({
                "status": "400",
                "error": error
            }), 400
        
        # Set session
        session['user_id'] = user_id
        session['username'] = username
        session['email'] = email
        session.permanent = True
        
        # Record connection
        models.User.record_connection(user_id, 'register', True)
        
        return jsonify({
            "status": "200",
            "data": {
                "user_id": user_id,
                "username": username,
                "email": email
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        data = request.get_json()
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username_or_email or not password:
            return jsonify({
                "status": "400",
                "error": "Username/email and password are required"
            }), 400
        
        user_id, username, email = models.User.authenticate_local_user(username_or_email, password)
        if not user_id:
            return jsonify({
                "status": "401",
                "error": "Invalid username/email or password"
            }), 401
        
        # Set session
        session['user_id'] = user_id
        session['username'] = username
        session['email'] = email
        session.permanent = True
        
        # Record connection
        models.User.record_connection(user_id, 'login', True)
        
        return jsonify({
            "status": "200",
            "data": {
                "user_id": user_id,
                "username": username,
                "email": email
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/auth/logout', methods=['POST'])
def logout():
    try:
        user_id = session.get('user_id')
        if user_id:
            models.User.record_connection(user_id, 'logout', False)
        session.clear()
        return jsonify({
            "status": "200",
            "message": "Logged out successfully"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/auth/verify', methods=['GET'])
def verify_session():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                "status": "401",
                "authenticated": False,
                "error": "Not authenticated"
            }), 401
        
        user = models.User.get_user_by_id(user_id)
        if not user:
            session.clear()
            return jsonify({
                "status": "401",
                "authenticated": False,
                "error": "User not found"
            }), 401
        
        return jsonify({
            "status": "200",
            "authenticated": True,
            "data": {
                "user_id": user.get("user_id"),
                "username": user.get("username"),
                "email": user.get("email"),
                "role": user.get("role", ""),
                "affiliation": user.get("affiliation", "")
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/user/record_connection', methods=['POST'])
def record_user_connection():
    try:
        user_id = request.args.get('user_id')
        event_type = request.args.get('event_type', 'login')
        if not user_id and request.is_json:
            data = request.get_json()
            user_id = data.get('user_id')
            event_type = data.get('event_type', 'login')
        
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "user_id is required"
            }), 400
        
        should_update_connection = event_type in ['login', 'page_load', 'page_visible']
        models.User.record_connection(user_id, event_type, should_update_connection)
        return jsonify({
            "status": "200",
            "message": f"Connection recorded successfully for event: {event_type}"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500



@endpoints_bp.route('/backend/user/last_connection', methods=['GET'])
def get_last_connection():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "user_id is required"
            }), 400        
        user_data = models.user_collection.find_one({"user_id": user_id})
        if user_data:
            last_connection = user_data.get("previous_connection") or user_data.get("last_connection")
            return jsonify({
                "status": "200",
                "data": {
                    "first_connection": user_data.get("first_connection").isoformat() if user_data.get("first_connection") else None,
                    "last_connection": last_connection.isoformat() if last_connection else None,
                    "last_event_type": user_data.get("last_event_type"),
                    "last_event_time": user_data.get("last_event_time").isoformat() if user_data.get("last_event_time") else None
                }
            }), 200
        else:
            return jsonify({
                "status": "200",
                "data": {
                    "first_connection": None,
                    "last_connection": None,
                    "last_event_type": None,
                    "last_event_time": None
                }
            }), 200
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500




@endpoints_bp.route('/backend/user/profile', methods=['GET'])
def get_user_profile():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "user_id is required"
            }), 400
        
        profile_data = models.User.get_user_profile(user_id)        
        if profile_data.get("first_connection"):
            profile_data["first_connection"] = profile_data["first_connection"].isoformat()
        if profile_data.get("last_connection"):
            profile_data["last_connection"] = profile_data["last_connection"].isoformat()
        
        return jsonify({
            "status": "200",
            "data": profile_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500



@endpoints_bp.route('/backend/user/profile', methods=['POST'])
def update_user_profile():
    try:
        user_id = request.args.get('user_id')
        role = request.args.get('role')
        affiliation = request.args.get('affiliation')
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "user_id is required"
            }), 400
        
        success = models.User.update_user_profile(user_id, role, affiliation)
        
        if success:
            return jsonify({
                "status": "200",
                "message": "Profile updated successfully"
            }), 200
        else:
            return jsonify({
                "status": "400",
                "error": "No valid data provided for update"
            }), 400
        
    except Exception as e:
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500
    
    

@endpoints_bp.route('/backend/user/preferences', methods=['GET', 'OPTIONS'])
def get_user_preferences():
    """Get user preferences including text provider"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "user_id is required"
            }), 400
        
        preferences = models.User.get_user_preferences(user_id)
        return jsonify({
            "status": "200",
            "data": preferences
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


@endpoints_bp.route('/backend/user/preferences', methods=['POST', 'OPTIONS'])
def save_user_preferences():
    """Save user preferences including text provider"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        text_provider = data.get('text_provider')
        
        if not user_id:
            return jsonify({
                "status": "400",
                "error": "user_id is required"
            }), 400
        
        if text_provider and text_provider not in ["ollama", "openai"]:
            return jsonify({
                "status": "400",
                "error": "text_provider must be 'ollama' or 'openai'"
            }), 400
        
        success, message = models.User.update_user_preferences(user_id, text_provider=text_provider)
        
        if success:
            return jsonify({
                "status": "200",
                "message": message,
                "data": models.User.get_user_preferences(user_id)
            }), 200
        else:
            return jsonify({
                "status": "400",
                "error": message
            }), 400
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "500",
            "error": str(e)
        }), 500


