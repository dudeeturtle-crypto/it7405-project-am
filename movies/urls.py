from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.home, name='home'),
    path('mongo-demo/', views.mongo_demo, name='mongo_demo'),
    path('movies/', views.movie_list, name='movie_list'),
    path('movies/<slug:slug>/', views.movie_detail, name='movie_detail'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    # Watchlist and favorite endpoints
    path('api/movies/<slug:slug>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    # Notifications endpoints
    path('notifications/', views.notifications_view, name='notifications'),
    path('api/notifications/<slug:movie_slug>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/support/read/', views.mark_notification_read, {'movie_slug': ''}, name='mark_support_notification_read'),
    # Support page
    path('support/', views.support_page, name='support'),
    # Custom Admin endpoints (using 'staff' prefix to avoid conflict with Django's /admin/)
    path('staff/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/manage-movies/', views.manage_movies, name='manage_movies'),
    path('staff/manage-tickets/', views.manage_tickets, name='manage_tickets'),
    path('staff/send-announcement/', views.send_announcement, name='send_announcement'),
]
