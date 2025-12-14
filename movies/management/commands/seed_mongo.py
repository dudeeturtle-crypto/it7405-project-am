from django.core.management.base import BaseCommand
from accounts.mongo_connection import get_db

class Command(BaseCommand):
    help = 'Seed sample documents into MongoDB reviews and movies collections (if enabled)'

    def handle(self, *args, **options):
        db = get_db()
        if db is None:
            self.stdout.write(self.style.WARNING('MongoDB is not enabled (USE_MONGODB=False). Aborting.'))
            return

        # Seed sample reviews
        reviews = db.reviews
        sample = [
            {
                'movie_slug': 'example-movie',
                'title': 'The Example Movie',
                'rating': 4.9,
                'body': 'A sample review for seeding.',
                'user': 'seed_user',
                'created_at': None,
            },
            {
                'movie_slug': 'another-movie',
                'title': 'Another',
                'rating': 2.3,
                'body': 'Loved it!',
                'user': 'seed_user',
                'created_at': None,
            }
        ]
        result = reviews.insert_many(sample)
        self.stdout.write(self.style.SUCCESS(f'Inserted {len(result.inserted_ids)} sample reviews'))

        # Seed a few sample movies into Mongo if the collection is empty
        try:
            movies_coll = db.movies
            if movies_coll.count_documents({}) == 0:
                sample_movies = [
                    {
                        'title': 'Rush Hour',
                        'slug': 'example-movie',
                        'description': 'An example seeded movie.',
                        'photo_url': 'https://tse3.mm.bing.net/th/id/OIP.Jpxv8g05O-UJhQceYe3BuAHaKk?rs=1&pid=ImgDetMain&o=7&rm=3',
                        'avg_rating': 4.9,
                        'review_count': 5,
                        'created_at': None,
                    },
                    {
                        'title': 'Another',
                        'slug': 'another-movie',
                        'description': 'Another seeded movie.',
                        'photo_url': 'https://d3tvwjfge35btc.cloudfront.net/Assets/11/824/L_p0027482411.jpg',
                        'avg_rating': 2.3,
                        'review_count': 0,
                        'created_at': None,
                    }
                ]
                for doc in sample_movies:
                    movies_coll.update_one({'slug': doc['slug']}, {'$set': doc}, upsert=True)
                self.stdout.write(self.style.SUCCESS(f'Seeded {len(sample_movies)} movies into MongoDB'))
            else:
                self.stdout.write(self.style.SUCCESS('Movies collection already contains documents; skipping movie seed.'))
            # Ensure the photo_url for the sample 'another-movie' is present even if we skipped seeding
            try:
                movies_coll.update_one(
                    {'slug': 'another-movie'},
                    {
                        '$set': {
                            'photo_url': 'https://d3tvwjfge35btc.cloudfront.net/Assets/11/824/L_p0027482411.jpg',
                            'title': 'Another',
                            'avg_rating': 2.3
                        },
                        '$setOnInsert': {
                            'title': 'Another',
                            'slug': 'another-movie',
                            'description': 'Another seeded movie.',
                            'avg_rating': 2.3,
                            'review_count': 0,
                            'created_at': None,
                        }
                    },
                    upsert=True
                )
            except Exception:
                pass
            # Ensure the photo_url for the sample 'example-movie' is present as well
            try:
                movies_coll.update_one(
                    {'slug': 'example-movie'},
                    {
                        '$set': {
                            'photo_url': 'https://tse3.mm.bing.net/th/id/OIP.Jpxv8g05O-UJhQceYe3BuAHaKk?rs=1&pid=ImgDetMain&o=7&rm=3',
                            'title': 'Rush Hour'
                        },
                        '$setOnInsert': {
                            'title': 'Rush Hour',
                            'slug': 'example-movie',
                            'description': 'An example seeded movie.',
                            'avg_rating': 0.0,
                            'review_count': 0,
                            'created_at': None,
                        }
                    },
                    upsert=True
                )
            except Exception:
                pass
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f'Could not seed movies into MongoDB: {exc}'))
