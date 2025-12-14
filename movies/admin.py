"""Admin for the movies app.

The `movies` app is now backed by MongoDB documents. To avoid Django trying
to manage SQL tables for `Movie` and `Review`, we do not register those models
with the admin. If you need an admin UI for Mongo documents, add a custom
admin view or a thin wrapper that queries Mongo.
"""
from django.contrib import admin

# Intentionally left blank: movie data lives in MongoDB now.

from django.contrib import admin
from .models import Movie, Review

admin.site.register(Movie)
admin.site.register(Review)

