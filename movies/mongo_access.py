from django.conf import settings
from django.forms.models import model_to_dict
from django.utils import timezone
from accounts.mongo_connection import get_db

try:
    # Import Django models for fallback and for syncing aggregates
    from .models import Movie, Review
except Exception:
    Movie = None
    Review = None


def _movie_to_dict(movie):
    if movie is None:
        return None
    if isinstance(movie, dict):
        return movie
    # Django model
    return {
        'id': movie.id,
        'title': movie.title,
        'slug': movie.slug,
        'description': getattr(movie, 'description', ''),
        'avg_rating': float(getattr(movie, 'avg_rating', 0) or 0),
        'review_count': int(getattr(movie, 'review_count', 0) or 0),
        'created_at': getattr(movie, 'created_at', None),
    }


def get_movies(q=None, sort=None, limit=None):
    """Return a list of movie dicts. Use Mongo when enabled, otherwise Django ORM."""
    db = get_db()
    if db is not None and settings.USE_MONGODB:
        query = {}
        if q:
            query['title'] = {'$regex': q, '$options': 'i'}
        cursor = db.movies.find(query, {'_id': 0})
        if sort == 'newest':
            cursor = cursor.sort('created_at', -1)
        elif sort == 'highest':
            cursor = cursor.sort('avg_rating', -1)
        elif sort == 'most_reviewed':
            cursor = cursor.sort('review_count', -1)
        if limit:
            cursor = cursor.limit(limit)
        results = list(cursor)
        # If Mongo enabled but empty result, fall back to Django ORM (useful in tests or when not yet synced)
        if not results and Movie is not None:
            qs = Movie.objects.all()
            if q:
                qs = qs.filter(title__icontains=q)
            if sort == 'newest':
                qs = qs.order_by('-created_at')
            elif sort == 'highest':
                qs = qs.order_by('-avg_rating')
            elif sort == 'most_reviewed':
                qs = qs.order_by('-review_count')
            if limit:
                qs = qs[:limit]
            return [_movie_to_dict(m) for m in qs]
        return results

    # Fallback to Django ORM
    if Movie is None:
        return []
    qs = Movie.objects.all()
    if q:
        qs = qs.filter(title__icontains=q)
    if sort == 'newest':
        qs = qs.order_by('-created_at')
    elif sort == 'highest':
        qs = qs.order_by('-avg_rating')
    elif sort == 'most_reviewed':
        qs = qs.order_by('-review_count')
    if limit:
        qs = qs[:limit]
    return [_movie_to_dict(m) for m in qs]


def get_movie_by_slug(slug):
    db = get_db()
    if db is not None and settings.USE_MONGODB:
        doc = db.movies.find_one({'slug': slug}, {'_id': 0})
        if doc:
            return doc
        # Fall back to SQL model if Mongo doesn't have the document yet
        if Movie is not None:
            try:
                movie = Movie.objects.get(slug=slug)
                return _movie_to_dict(movie)
            except Movie.DoesNotExist:
                return None
    if Movie is None:
        return None
    try:
        movie = Movie.objects.get(slug=slug)
        return _movie_to_dict(movie)
    except Movie.DoesNotExist:
        return None


def get_reviews_for_movie(movie_slug, limit=None, page=None, per_page=5):
    """Return reviews (list of dicts) for a movie identified by slug."""
    db = get_db()
    if db is not None and settings.USE_MONGODB:
        cursor = db.reviews.find({'movie_slug': movie_slug}, {'_id': 0}).sort('created_at', -1)
        if limit:
            cursor = cursor.limit(limit)
        if page is not None:
            skip = (page - 1) * per_page
            cursor = cursor.skip(skip).limit(per_page)
        return list(cursor)

    # Fallback: Django ORM
    if Review is None:
        return []
    qs = Review.objects.filter(movie__slug=movie_slug).order_by('-created_at')
    if page is not None:
        start = (page - 1) * per_page
        end = start + per_page
        qs = qs[start:end]
    return [model_to_dict(r, fields=[f.name for f in r._meta.fields if f.name != 'id']) for r in qs]


def upsert_review(movie_slug, user, rating, title, body):
    """Insert or update a review in Mongo. Also updates SQL movie aggregates if Movie model exists."""
    db = get_db()
    now = timezone.now().isoformat()
    username = getattr(user, 'username', str(user))
    if db is not None and settings.USE_MONGODB:
        reviews = db.reviews
        filter_q = {'movie_slug': movie_slug, 'user': username}
        update = {
            '$set': {
                'rating': int(rating),
                'title': title,
                'body': body,
                'updated_at': now,
            },
            '$setOnInsert': {
                'movie_slug': movie_slug,
                'user': username,
                'created_at': now,
            }
        }
        result = reviews.update_one(filter_q, update, upsert=True)

        # Recompute aggregates from Mongo and sync to SQL Movie if present
        try:
            pipeline = [
                {'$match': {'movie_slug': movie_slug}},
                {'$group': {'_id': '$movie_slug', 'avg': {'$avg': '$rating'}, 'count': {'$sum': 1}}}
            ]
            agg = list(reviews.aggregate(pipeline))
            if agg:
                avg = float(agg[0]['avg'])
                count = int(agg[0]['count'])
                # Update SQL Movie model if present
                if Movie is not None:
                    Movie.objects.filter(slug=movie_slug).update(avg_rating=avg, review_count=count)
                # Also keep the Mongo movies collection in sync with aggregates
                try:
                    db.movies.update_one({'slug': movie_slug}, {'$set': {'avg_rating': avg, 'review_count': count}})
                except Exception:
                    pass
        except Exception:
            pass

        return {'upserted': getattr(result, 'upserted_id', None), 'matched_count': result.matched_count, 'modified_count': result.modified_count}

    # Fallback: use Django ORM
    if Review is None or Movie is None:
        return None
    try:
        movie = Movie.objects.get(slug=movie_slug)
    except Movie.DoesNotExist:
        return None
    review_obj, created = Review.objects.update_or_create(
        user=user, movie=movie,
        defaults={'rating': rating, 'body': body}
    )
    # update aggregates on Movie model
    try:
        from django.db.models import Avg, Count
        agg = Review.objects.filter(movie=movie).aggregate(avg=Avg('rating'), count=Count('id'))
        movie.avg_rating = agg['avg'] or 0
        movie.review_count = agg['count'] or 0
        movie.save(update_fields=['avg_rating', 'review_count'])
    except Exception:
        pass
    return {'created': created}


# ========== WATCHLIST / FAVORITES ==========

def add_to_watchlist(username, movie_slug, movie_title):
    """Add a movie to user's watchlist in Mongo. Returns True if added, False if already exists."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        watchlists = db.watchlists
        now = timezone.now().isoformat()
        filter_q = {'username': username, 'movie_slug': movie_slug}
        # Check if already exists
        existing = watchlists.find_one(filter_q)
        if existing:
            return False  # Already in watchlist
        result = watchlists.insert_one({
            'username': username,
            'movie_slug': movie_slug,
            'movie_title': movie_title,
            'added_at': now,
            'is_favorite': True,
        })
        return bool(result.inserted_id)
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
        return False


def remove_from_watchlist(username, movie_slug):
    """Remove a movie from user's watchlist. Returns True if removed, False if not found."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        result = db.watchlists.delete_one({'username': username, 'movie_slug': movie_slug})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        return False


def is_in_watchlist(username, movie_slug):
    """Check if a movie is in user's watchlist."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        return db.watchlists.find_one({'username': username, 'movie_slug': movie_slug}) is not None
    except Exception:
        return False


def get_user_watchlist(username):
    """Get all movies in user's watchlist."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return []
    try:
        return list(db.watchlists.find({'username': username}, {'_id': 0}).sort('added_at', -1))
    except Exception:
        return []


# ========== VIEW HISTORY ==========

def log_movie_view(username, movie_slug, movie_title):
    """Log a user's view of a movie in Mongo. Updates view count if already seen."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        view_history = db.view_history
        now = timezone.now().isoformat()
        filter_q = {'username': username, 'movie_slug': movie_slug}
        result = view_history.update_one(
            filter_q,
            {
                '$set': {
                    'username': username,
                    'movie_slug': movie_slug,
                    'movie_title': movie_title,
                    'last_viewed_at': now,
                },
                '$inc': {'view_count': 1},
                '$setOnInsert': {
                    'first_viewed_at': now,
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error logging movie view: {e}")
        return False


def get_user_view_history(username, limit=20):
    """Get user's recent movie view history."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return []
    try:
        return list(db.view_history.find({'username': username}, {'_id': 0}).sort('last_viewed_at', -1).limit(limit))
    except Exception:
        return []


# ========== NOTIFICATIONS ==========

def create_notification(username, movie_slug, movie_title, review_rating, review_title, notification_type='new_review'):
    """Create a notification for a user when a high-rated review is posted."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        notification = {
            'username': username,
            'movie_slug': movie_slug,
            'movie_title': movie_title,
            'review_rating': review_rating,
            'review_title': review_title,
            'notification_type': notification_type,
            'created_at': timezone.now().isoformat(),
            'is_read': False,
        }
        result = db.notifications.insert_one(notification)
        return result.inserted_id is not None
    except Exception as e:
        print(f"Error creating notification: {e}")
        return False


def get_user_notifications(username, unread_only=False):
    """Get notifications for a user."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return []
    try:
        query = {'username': username}
        if unread_only:
            query['is_read'] = False
        return list(db.notifications.find(query, {'_id': 0}).sort('created_at', -1))
    except Exception:
        return []


def mark_notification_as_read(username, movie_slug):
    """Mark notifications for a movie as read."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        result = db.notifications.update_many(
            {'username': username, 'movie_slug': movie_slug},
            {'$set': {'is_read': True}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return False


def check_and_notify_watchlist_owners(movie_slug, movie_title, review_rating, review_title):
    """
    Check all users who have this movie in their watchlist.
    If review rating >= 4.5, create notifications for them.
    """
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return 0
    
    try:
        # Only notify for highly-rated reviews (4.5+)
        if review_rating < 4.5:
            return 0
        
        # Find all users who have this movie in their watchlist
        watchlist_entries = list(db.watchlists.find({'movie_slug': movie_slug}, {'username': 1}))
        notification_count = 0
        
        for entry in watchlist_entries:
            username = entry.get('username')
            if username:
                success = create_notification(
                    username=username,
                    movie_slug=movie_slug,
                    movie_title=movie_title,
                    review_rating=review_rating,
                    review_title=review_title,
                    notification_type='new_review'
                )
                if success:
                    notification_count += 1
        
        return notification_count
    except Exception as e:
        print(f"Error checking watchlist owners for notifications: {e}")
        return 0


# ========== SUPPORT TICKETS ==========

def create_support_ticket(username, email, subject, message):
    """Create a new support ticket."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        ticket = {
            'username': username,
            'email': email,
            'subject': subject,
            'message': message,
            'created_at': timezone.now().isoformat(),
            'status': 'open',  # open, in_progress, resolved, closed
            'responses': [],  # List of admin responses
        }
        result = db.support_tickets.insert_one(ticket)
        return str(result.inserted_id) if result.inserted_id else False
    except Exception as e:
        print(f"Error creating support ticket: {e}")
        return False


def get_support_tickets(admin_view=False, status_filter=None):
    """Get all support tickets (admin view) or user's tickets."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return []
    try:
        query = {}
        if status_filter:
            query['status'] = status_filter
        cursor = db.support_tickets.find(query, {'_id': 0}).sort('created_at', -1)
        return list(cursor)
    except Exception:
        return []


def get_user_support_tickets(username):
    """Get support tickets for a specific user."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return []
    try:
        return list(db.support_tickets.find({'username': username}, {'_id': 0}).sort('created_at', -1))
    except Exception:
        return []


def add_ticket_response(subject, response_text, admin_username):
    """Add admin response to a support ticket."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        response = {
            'admin_username': admin_username,
            'response_text': response_text,
            'responded_at': timezone.now().isoformat(),
        }
        result = db.support_tickets.update_one(
            {'subject': subject},
            {
                '$push': {'responses': response},
                '$set': {'status': 'in_progress'}
            }
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error adding ticket response: {e}")
        return False


def close_support_ticket(subject):
    """Close a support ticket."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        result = db.support_tickets.update_one(
            {'subject': subject},
            {'$set': {'status': 'closed'}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error closing ticket: {e}")
        return False


def notify_user_on_ticket_response(username, ticket_subject, admin_response_text):
    """Create a notification when admin responds to a support ticket."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        notification = {
            'username': username,
            'title': f'Support Response: {ticket_subject}',
            'message': admin_response_text[:100] + '...' if len(admin_response_text) > 100 else admin_response_text,
            'notification_type': 'support_response',
            'ticket_subject': ticket_subject,
            'created_at': timezone.now().isoformat(),
            'is_read': False,
        }
        result = db.notifications.insert_one(notification)
        return result.inserted_id is not None
    except Exception as e:
        print(f"Error creating support response notification: {e}")
        return False


# ========== ADMIN BROADCAST NOTIFICATIONS ==========

def send_broadcast_notification(title, message, notification_type='announcement'):
    """Send notification to all users."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return 0
    try:
        # Get all unique users
        users = list(db.notifications.distinct('username'))
        # Also include watchlist users
        watchlist_users = list(db.watchlists.distinct('username'))
        all_users = list(set(users + watchlist_users))
        
        notification_count = 0
        for username in all_users:
            notification = {
                'username': username,
                'title': title,
                'message': message,
                'notification_type': notification_type,
                'created_at': timezone.now().isoformat(),
                'is_read': False,
            }
            try:
                db.broadcast_notifications.insert_one(notification)
                notification_count += 1
            except Exception:
                pass
        
        return notification_count
    except Exception as e:
        print(f"Error sending broadcast notification: {e}")
        return 0


def get_broadcast_notifications(username):
    """Get broadcast notifications for a user."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return []
    try:
        return list(db.broadcast_notifications.find({'username': username}, {'_id': 0}).sort('created_at', -1))
    except Exception:
        return []


# ========== MOVIE MANAGEMENT (ADMIN) ==========

def create_movie(title, slug, description, director, year, cast=None, photo_url=None):
    """Create a new movie (admin only)."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        movie = {
            'title': title,
            'slug': slug,
            'description': description,
            'director': director,
            'year': year,
            'cast': cast or [],
            'photo_url': photo_url,
            'avg_rating': 0,
            'review_count': 0,
            'created_at': timezone.now().isoformat(),
        }
        result = db.movies.insert_one(movie)
        return result.inserted_id is not None
    except Exception as e:
        print(f"Error creating movie: {e}")
        return False


def update_movie(slug, **kwargs):
    """Update a movie (admin only)."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        # Remove slug from kwargs if present
        update_data = {k: v for k, v in kwargs.items() if k != 'slug'}
        result = db.movies.update_one(
            {'slug': slug},
            {'$set': update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating movie: {e}")
        return False


def delete_movie(slug):
    """Delete a movie (admin only)."""
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return False
    try:
        result = db.movies.delete_one({'slug': slug})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting movie: {e}")
        return False
