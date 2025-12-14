from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.conf import settings
from .forms import ReviewForm
from django.contrib.auth.models import User
from accounts.mongo_connection import get_db
from .mongo_access import (
    get_movies,
    get_movie_by_slug,
    get_reviews_for_movie,
    upsert_review,
    add_to_watchlist,
    remove_from_watchlist,
    is_in_watchlist,
    get_user_watchlist,
    log_movie_view,
    get_user_view_history,
    create_notification,
    get_user_notifications,
    mark_notification_as_read,
    check_and_notify_watchlist_owners,
    create_support_ticket,
    get_support_tickets,
    get_user_support_tickets,
    add_ticket_response,
    close_support_ticket,
    notify_user_on_ticket_response,
    send_broadcast_notification,
    get_broadcast_notifications,
    create_movie,
    update_movie,
    delete_movie,
)


def is_admin(request):
    """Check if user is admin."""
    db = get_db()
    if db is None:
        return False
    
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = request.session.get('username')
    
    if not username:
        return False
    
    try:
        user = db.users.find_one({'username': username})
        return user and user.get('is_admin', False)
    except Exception:
        return False


def home(request):
    featured = get_movies(sort='highest', limit=6)
    latest = get_movies(sort='newest', limit=6)
    top_rated = get_movies(sort='highest', limit=6)
    context = {'featured': featured, 'latest': latest, 'top_rated': top_rated}
    # If Mongo is enabled, add a small sample of Mongo reviews to the context
    mongo_db = get_db()
    if mongo_db is not None:
        try:
            mongo_reviews = list(mongo_db.reviews.find({}, {'_id': 0}).limit(5))
        except Exception:
            mongo_reviews = []
        context['mongo_reviews'] = mongo_reviews
    return render(request, 'movies/home.html', context)


def movie_list(request):
    q = request.GET.get('q')
    sort = request.GET.get('sort')
    # Use Mongo helper (falls back to ORM)
    movies = get_movies(q=q, sort=sort)
    paginator = Paginator(movies, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'movies/movie_list.html', {'page_obj': page_obj})


def movie_detail(request, slug):
    movie = get_movie_by_slug(slug)
    if movie is None:
        raise Http404('Movie not found')

    # Determine username from Django auth or session fallback
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = request.session.get('username')
    
    # Log view history if user is authenticated
    if username:
        log_movie_view(username, slug, movie.get('title', slug))

    page_number = request.GET.get('page')
    page = int(page_number) if page_number and page_number.isdigit() else 1
    reviews = get_reviews_for_movie(movie_slug=slug, page=page, per_page=5)

    # Check if user has favorited this movie
    is_favorited = False
    if username:
        is_favorited = is_in_watchlist(username, slug)

    # Determine if the user has a review (Mongo or ORM fallback)
    user_review = None
    if request.user.is_authenticated:
        mongo_db = get_db()
        if mongo_db is not None and request.method != 'POST':
            try:
                user_review_doc = mongo_db.reviews.find_one({'movie_slug': slug, 'user': request.user.username}, {'_id': 0})
                if user_review_doc:
                    user_review = user_review_doc
            except Exception:
                user_review = None

    if request.method == 'POST':
        # Check MongoDB authentication (from session)
        mongo_username = request.session.get('username')
        if not mongo_username:
            messages.error(request, 'Please login to submit a review.')
            return redirect('accounts:login')
        form = ReviewForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # If Mongo enabled, upsert into Mongo
            if get_db() is not None:
                upsert_review(slug, mongo_username, cd.get('rating'), cd.get('title'), cd.get('body'))
                
                # Check if this is a high-rated review and notify watchlist owners
                if cd.get('rating') >= 4.5:
                    check_and_notify_watchlist_owners(
                        movie_slug=slug,
                        movie_title=movie.get('title', slug),
                        review_rating=cd.get('rating'),
                        review_title=cd.get('title')
                    )
                
                # If this is an AJAX request, return JSON with the saved review
                is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
                if is_ajax:
                    try:
                        db = get_db()
                        saved = db.reviews.find_one({'movie_slug': slug, 'user': mongo_username}, {'_id': 0})
                        return JsonResponse({'status': 'ok', 'review': saved})
                    except Exception:
                        return JsonResponse({'status': 'error', 'message': 'Saved but could not retrieve review.'}, status=500)
                messages.success(request, 'Your review has been saved.')
                return redirect('movies:movie_detail', slug=slug)
            # otherwise fall back to ORM behaviour
            # (existing form.save logic kept for fallback)
            try:
                from .models import Movie as MovieModel, Review as ReviewModel
                movie_obj = MovieModel.objects.get(slug=slug)
                # update or create
                review_obj, created = ReviewModel.objects.update_or_create(
                    user=request.user, movie=movie_obj,
                    defaults={'rating': cd.get('rating'), 'title': cd.get('title'), 'body': cd.get('body')}
                )
                messages.success(request, 'Your review has been saved.')
                return redirect('movies:movie_detail', slug=slug)
            except Exception:
                messages.error(request, 'Could not save review.')
    else:
        if user_review and isinstance(user_review, dict):
            form = ReviewForm(initial={'rating': user_review.get('rating'), 'title': user_review.get('title'), 'body': user_review.get('body')})
        else:
            form = ReviewForm()

    context = {
        'movie': movie,
        'reviews': reviews,
        'form': form,
        'user_review': user_review,
        'is_favorited': is_favorited,
    }
    return render(request, 'movies/movie_detail.html', context)


def profile_view(request, username):
    user = User.objects.filter(username=username).first()
    if not user:
        raise Http404('User not found')

    # Try Mongo first
    mongo_db = get_db()
    reviews = []
    if mongo_db is not None:
        try:
            reviews = list(mongo_db.reviews.find({'user': username}, {'_id': 0}).sort('created_at', -1))
        except Exception:
            reviews = []
    else:
        # Fallback to ORM
        try:
            from .models import Review as ReviewModel
            reviews = list(ReviewModel.objects.filter(user=user).select_related('movie').order_by('-created_at'))
        except Exception:
            reviews = []

    paginator = Paginator(reviews, 10)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request, 'movies/profile.html', {'profile_user': user, 'page_obj': page_obj})

def mongo_demo(request):
    """Simple demo view that shows a few Mongo reviews when enabled."""
    mongo_db = get_db()
    mongo_reviews = []
    if mongo_db is not None:
        try:
            mongo_reviews = list(mongo_db.reviews.find({}, {'_id': 0}).limit(20))
        except Exception:
            mongo_reviews = []
    return render(request, 'movies/mongo_demo.html', {'mongo_reviews': mongo_reviews})


# ========== WATCHLIST / FAVORITE ENDPOINTS ==========

def toggle_favorite(request, slug):
    """AJAX endpoint to toggle favorite status of a movie. Returns JSON."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        # Try session-based username (MongoDB fallback)
        username = request.session.get('username')
        if not username:
            return JsonResponse({'status': 'error', 'message': 'Not authenticated'}, status=401)
    else:
        username = request.user.username
    
    movie = get_movie_by_slug(slug)
    if movie is None:
        return JsonResponse({'status': 'error', 'message': 'Movie not found'}, status=404)
    
    movie_title = movie.get('title', slug)
    
    # Check if already in watchlist
    if is_in_watchlist(username, slug):
        # Remove from watchlist
        success = remove_from_watchlist(username, slug)
        return JsonResponse({
            'status': 'ok',
            'action': 'removed',
            'is_favorited': False,
            'message': 'Removed from watchlist'
        })
    else:
        # Add to watchlist
        success = add_to_watchlist(username, slug, movie_title)
        if success:
            return JsonResponse({
                'status': 'ok',
                'action': 'added',
                'is_favorited': True,
                'message': 'Added to watchlist'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Could not add to watchlist'
            }, status=500)


def watchlist_view(request):
    """Display user's watchlist."""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        # Try to get username from session (for MongoDB users)
        username = request.session.get('username')
        if not username:
            return redirect('accounts:login')
    else:
        username = request.user.username
    
    watchlist = get_user_watchlist(username)
    view_history = get_user_view_history(username, limit=10)
    
    paginator = Paginator(watchlist, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'view_history': view_history,
        'watchlist_count': len(watchlist),
    }
    return render(request, 'movies/watchlist.html', context)


# ========== NOTIFICATIONS ==========

def notifications_view(request):
    """Display user's notifications."""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        username = request.session.get('username')
        if not username:
            return redirect('accounts:login')
    else:
        username = request.user.username
    
    notifications = get_user_notifications(username)
    unread_count = len([n for n in notifications if not n.get('is_read')])
    
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'unread_count': unread_count,
        'total_count': len(notifications),
    }
    return render(request, 'movies/notifications.html', context)


def mark_notification_read(request, movie_slug):
    """Mark notifications as read (AJAX endpoint)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    if not request.user.is_authenticated:
        username = request.session.get('username')
        if not username:
            return JsonResponse({'status': 'error', 'message': 'Not authenticated'}, status=401)
    else:
        username = request.user.username
    
    # Handle both movie notifications and support response notifications
    db = get_db()
    if db is None or not settings.USE_MONGODB:
        return JsonResponse({'status': 'error', 'message': 'Database unavailable'}, status=500)
    
    try:
        # Try to mark as read - works for both movie_slug and ticket_subject
        if movie_slug:
            # For review notifications (movie_slug not empty)
            result = db.notifications.update_many(
                {'username': username, 'movie_slug': movie_slug},
                {'$set': {'is_read': True}}
            )
        else:
            # For support notifications (movie_slug is empty, use ticket_subject)
            ticket_subject = request.POST.get('ticket_subject', '')
            result = db.notifications.update_many(
                {'username': username, 'ticket_subject': ticket_subject},
                {'$set': {'is_read': True}}
            )
        
        success = result.modified_count > 0
        return JsonResponse({
            'status': 'ok' if success else 'error',
            'message': 'Notification marked as read' if success else 'Could not mark as read'
        })
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ========== SUPPORT PAGE ==========

def support_page(request):
    """Display support page where users can submit issues."""
    if not request.user.is_authenticated:
        username = request.session.get('username')
        if not username:
            return redirect('accounts:login')
    else:
        username = request.user.username
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        email = request.POST.get('email', '').strip()
        
        if not subject or not message or not email:
            messages.error(request, 'All fields are required.')
            return redirect('movies:support')
        
        ticket_id = create_support_ticket(username, email, subject, message)
        if ticket_id:
            messages.success(request, 'Your support ticket has been submitted. We will respond shortly.')
            return redirect('movies:support')
        else:
            messages.error(request, 'Failed to submit ticket. Please try again.')
            return redirect('movies:support')
    
    # Get user's tickets
    user_tickets = get_user_support_tickets(username)
    
    paginator = Paginator(user_tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_tickets': len(user_tickets),
    }
    return render(request, 'movies/support.html', context)


# ========== ADMIN DASHBOARD ==========

def admin_dashboard(request):
    """Admin dashboard for managing movies, notifications, and support tickets."""
    if not is_admin(request):
        messages.error(request, 'Access denied. Admin only.')
        return redirect('movies:home')
    
    # Get statistics
    db = get_db()
    movies_count = db.movies.count_documents({})
    users_count = db.watchlists.distinct('username').__len__() if hasattr(db.watchlists.distinct('username'), '__len__') else len(list(db.watchlists.distinct('username')))
    open_tickets = len(get_support_tickets(status_filter='open'))
    
    context = {
        'movies_count': movies_count,
        'users_count': users_count,
        'open_tickets': open_tickets,
    }
    return render(request, 'movies/admin_dashboard.html', context)


# ========== MOVIE MANAGEMENT ==========

def manage_movies(request):
    """Admin page to manage movies."""
    if not is_admin(request):
        messages.error(request, 'Access denied. Admin only.')
        return redirect('movies:home')
    
    movies_list = get_movies(limit=100)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            title = request.POST.get('title', '').strip()
            slug = request.POST.get('slug', '').strip()
            description = request.POST.get('description', '').strip()
            director = request.POST.get('director', '').strip()
            year = request.POST.get('year', '').strip()
            photo_url = request.POST.get('photo_url', '').strip()
            
            if all([title, slug, description, director, year]):
                success = create_movie(title, slug, description, director, int(year), photo_url=photo_url if photo_url else None)
                if success:
                    messages.success(request, f'Movie "{title}" created successfully.')
                else:
                    messages.error(request, 'Failed to create movie.')
            else:
                messages.error(request, 'All fields are required.')
            
            return redirect('movies:manage_movies')
        
        elif action == 'delete':
            slug = request.POST.get('slug', '').strip()
            if slug:
                success = delete_movie(slug)
                if success:
                    messages.success(request, 'Movie deleted successfully.')
                else:
                    messages.error(request, 'Failed to delete movie.')
            
            return redirect('movies:manage_movies')
    
    paginator = Paginator(movies_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'movies/manage_movies.html', context)


# ========== MANAGE SUPPORT TICKETS ==========

def manage_tickets(request):
    """Admin page to manage support tickets."""
    if not is_admin(request):
        messages.error(request, 'Access denied. Admin only.')
        return redirect('movies:home')
    
    status_filter = request.GET.get('status', 'open')
    tickets = get_support_tickets(status_filter=status_filter if status_filter else None)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        subject = request.POST.get('subject', '').strip()
        
        if action == 'respond':
            response_text = request.POST.get('response_text', '').strip()
            if subject and response_text:
                username = request.session.get('username') or request.user.username
                success = add_ticket_response(subject, response_text, username)
                if success:
                    messages.success(request, 'Response added to ticket.')
                    
                    # Get the ticket to find the user who submitted it
                    try:
                        db = get_db()
                        ticket = db.support_tickets.find_one({'subject': subject})
                        if ticket:
                            ticket_username = ticket.get('username')
                            # Notify the user that admin responded
                            notify_user_on_ticket_response(ticket_username, subject, response_text)
                    except Exception as e:
                        print(f"Error notifying user: {e}")
                else:
                    messages.error(request, 'Failed to add response.')
        
        elif action == 'close':
            if subject:
                success = close_support_ticket(subject)
                if success:
                    messages.success(request, 'Ticket closed.')
                else:
                    messages.error(request, 'Failed to close ticket.')
        
        # Redirect back to the manage_tickets page with the status filter preserved
        url = f"{reverse('movies:manage_tickets')}?status={status_filter}"
        return redirect(url)
    
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'statuses': ['open', 'in_progress', 'resolved', 'closed'],
    }
    return render(request, 'movies/manage_tickets.html', context)


# ========== SEND BROADCAST NOTIFICATION ==========

def send_announcement(request):
    """Admin page to send broadcast notifications."""
    if not is_admin(request):
        messages.error(request, 'Access denied. Admin only.')
        return redirect('movies:home')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        
        if title and message:
            count = send_broadcast_notification(title, message, notification_type='announcement')
            messages.success(request, f'Announcement sent to {count} users.')
            return redirect('movies:send_announcement')
        else:
            messages.error(request, 'Title and message are required.')
    
    return render(request, 'movies/send_announcement.html')
