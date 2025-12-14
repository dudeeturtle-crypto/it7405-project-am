"""
Context processor to make user data available in all templates
"""
from .mongo_users import get_user_by_email


def user_context(request):
    """Add user data to template context"""
    user = None
    is_authenticated = False
    unread_notifications_count = 0
    is_admin = False
    
    # Check if user is logged in via session
    # Check for 'username' in session (more reliable than email/user_id)
    if 'username' in request.session:
        is_authenticated = True
        user = {
            'username': request.session.get('username'),
            'email': request.session.get('email'),
            'user_id': request.session.get('user_id'),
        }
        
        # Get unread notifications count
        try:
            from movies.mongo_access import get_user_notifications
            username = request.session.get('username')
            if username:
                notifications = get_user_notifications(username, unread_only=True)
                unread_notifications_count = len(notifications)
        except Exception:
            unread_notifications_count = 0
        
        # Check if user is admin
        try:
            from accounts.mongo_connection import get_db
            db = get_db()
            username = request.session.get('username')
            if db and username:
                admin_user = db.users.find_one({'username': username})
                is_admin = admin_user and admin_user.get('is_admin', False)
        except Exception:
            is_admin = False
    
    return {
        'mongo_user': user,
        'mongo_is_authenticated': is_authenticated,
        'unread_notifications_count': unread_notifications_count,
        'is_admin': is_admin,
    }
