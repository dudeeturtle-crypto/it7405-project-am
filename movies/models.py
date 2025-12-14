from django.db import models
from django.utils.text import slugify


def slugify_title(title):
    """Utility: create URL-friendly slug from title"""
    return slugify(title)[:200]


class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    release_year = models.IntegerField()

    # ⭐ REQUIRED for sorting movies
    avg_rating = models.FloatField(default=0.0)

    def __str__(self):
        return self.title


class Review(models.Model):
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    reviewer_name = models.CharField(max_length=100)
    rating = models.IntegerField()
    comment = models.TextField()

    def __str__(self):
        return f"{self.movie.title} - {self.rating}"
