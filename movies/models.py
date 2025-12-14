"""Movies SQL models removed.

This project switched the `movies` app to store its data in MongoDB.
The original Django ORM `Movie` and `Review` models have been intentionally
removed to prevent Django from creating and managing SQL tables for them.

If you need a slug helper or other small utilities, re-add them here as
non-model functions. Keep in mind that Django admin/auth still rely on the
project's default SQL database for users and sessions.
"""

def slugify_title(title):
    """Utility: a simple slugify helper used when creating movie documents."""
    from django.utils.text import slugify
    base = slugify(title)[:200]
    return base

from django.db import models

class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    release_year = models.IntegerField()

    def __str__(self):
        return self.title


class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    reviewer_name = models.CharField(max_length=100)
    rating = models.IntegerField()
    comment = models.TextField()

    def __str__(self):
        return f"{self.movie.title} - {self.rating}"
