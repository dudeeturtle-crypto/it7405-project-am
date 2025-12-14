"""
MongoDB user authentication and management
Stores user credentials in MongoDB instead of Django's auth system
"""
import hashlib
import os
from datetime import datetime
from pymongo import MongoClient
from django.conf import settings


def get_user_db():
    """Get MongoDB database for user management"""
    if not getattr(settings, 'USE_MONGODB', False):
        return None
    
    try:
        mongo_uri = getattr(settings, 'MONGODB_URI', 'mongodb://localhost:27017')
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[getattr(settings, 'MONGODB_NAME', 'moviereviews_db')]
        # Verify connection
        db.command('ping')
        return db
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        return None


def hash_password(password):
    """Hash password using PBKDF2-like approach (simple but effective for this use)"""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), b'moviereviews', 100000).hex()


def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed


def user_exists(email):
    """Check if user email already exists"""
    db = get_user_db()
    if db is None:
        return False
    
    user = db.users.find_one({'email': email.lower()})
    return user is not None


def username_exists(username):
    """Check if username already exists"""
    db = get_user_db()
    if db is None:
        return False
    
    user = db.users.find_one({'username': username})
    return user is not None


def create_user(username, email, password):
    """Create a new user in MongoDB"""
    db = get_user_db()
    if db is None:
        raise Exception("MongoDB not available")
    
    email_lower = email.lower()
    
    # Check if user already exists
    if user_exists(email_lower) or username_exists(username):
        return None
    
    user_doc = {
        'username': username,
        'email': email_lower,
        'password_hash': hash_password(password),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'is_active': True
    }
    
    result = db.users.insert_one(user_doc)
    return result.inserted_id


def authenticate_user(email, password):
    """Authenticate user by email and password"""
    db = get_user_db()
    if db is None:
        return None
    
    user = db.users.find_one({'email': email.lower(), 'is_active': True})
    
    if user and verify_password(password, user['password_hash']):
        return user
    
    return None


def get_user_by_email(email):
    """Get user document by email"""
    db = get_user_db()
    if db is None:
        return None
    
    return db.users.find_one({'email': email.lower()})


def get_user_by_id(user_id):
    """Get user document by MongoDB ObjectId"""
    from bson import ObjectId
    
    db = get_user_db()
    if db is None:
        return None
    
    try:
        return db.users.find_one({'_id': ObjectId(user_id)})
    except:
        return None


def get_user_by_username(username):
    """Get user document by username"""
    db = get_user_db()
    if db is None:
        return None
    
    return db.users.find_one({'username': username})


def update_user(email, **kwargs):
    """Update user document"""
    db = get_user_db()
    if db is None:
        return False
    
    kwargs['updated_at'] = datetime.utcnow()
    result = db.users.update_one(
        {'email': email.lower()},
        {'$set': kwargs}
    )
    return result.modified_count > 0


def delete_user(email):
    """Delete user account"""
    db = get_user_db()
    if db is None:
        return False
    
    result = db.users.delete_one({'email': email.lower()})
    return result.deleted_count > 0
