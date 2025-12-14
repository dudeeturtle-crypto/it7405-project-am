from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.account_urls')),
    path('', include('movies.urls')),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),
]
