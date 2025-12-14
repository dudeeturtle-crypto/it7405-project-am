from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.mongo_connection import get_db
from .mongo_access import upsert_review


class MovieReviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('u1', password='pass')
        # Ensure a movie doc exists in Mongo for the tests
        db = get_db()
        if db is None:
            self.skipTest('MongoDB not enabled for tests')
        self.movie_slug = 't1'
        db.movies.update_one({'slug': self.movie_slug}, {'$set': {'title': 'T1', 'slug': self.movie_slug, 'avg_rating': 0.0, 'review_count': 0}}, upsert=True)

    def test_create_review_updates_movie_rating(self):
        upsert_review(self.movie_slug, self.user, 5, 'Great', 'Great movie')
        db = get_db()
        m = db.movies.find_one({'slug': self.movie_slug})
        self.assertIsNotNone(m)
        self.assertEqual(int(m.get('review_count', 0)), 1)
        self.assertEqual(float(m.get('avg_rating', 0)), 5.0)

    def test_anonymous_cannot_post_review_via_view(self):
        c = Client()
        url = f'/movies/{self.movie_slug}/'
        response = c.post(url, {'rating': 4, 'title': 't', 'body': 'b'})
        # Should redirect to login
        self.assertIn(response.status_code, (302, 301))
