from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from movies.models import Movie, Review
import random
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seed sample movies, users and reviews (multiple items)'

    def handle(self, *args, **options):
        # Ensure test users exist (create if missing)
        users = []
        if User.objects.filter(username='testuser').exists():
            users.append(User.objects.get(username='testuser'))
        else:
            users.append(User.objects.create_user('testuser', password='password123'))

        for i in range(1, 6):
            username = f'user{i}'
            if User.objects.filter(username=username).exists():
                users.append(User.objects.get(username=username))
            else:
                users.append(User.objects.create_user(username, password='password123'))

        sample_movies = [
            ("Neon Skies", 2021, ["Sci-Fi", "Drama"], "A visually stunning journey across the future city."),
            ("Quiet Harbor", 2019, ["Drama", "Mystery"], "A small town hides big secrets beneath the surface."),
            ("Laugh Track", 2020, ["Comedy"], "A stand-up comedian navigates life and love."),
            ("Midnight Run", 2017, ["Action", "Thriller"], "A courier with a secret package races the clock."),
            ("The Last Note", 2022, ["Romance", "Music"], "Two musicians write their final symphony."),
            ("Echoes", 2016, ["Horror"], "Whispers in an abandoned facility awaken old fears."),
            ("Wilderness", 2015, ["Adventure"], "An expedition into the unknown tests friendship."),
            ("Circuit", 2023, ["Sci-Fi", "Action"], "Racing drones and corporate espionage collide."),
            ("Palette", 2018, ["Documentary"], "Artists reinvent their world through color."),
            ("Homefront", 2020, ["Drama"], "A family's resilience during turbulent times."),
        ]

        # Create movies if they don't already exist
        created = []
        idx = 1
        for title, year, genres, desc in sample_movies:
            if Movie.objects.filter(title=title).exists():
                idx += 1
                continue
            poster = f'https://picsum.photos/seed/movie{idx}/400/600'
            movie = Movie.objects.create(
                title=title,
                year=year,
                duration_minutes=random.choice([90, 100, 110, 120, 130]),
                genres=genres,
                director=f'Director {idx}',
                cast=[f'Actor {idx}A', f'Actor {idx}B'],
                description=desc,
                poster_url=poster,
            )
            created.append(movie)
            idx += 1

        # create random reviews for newly created movies
        for movie in created:
            num_reviews = random.randint(1, 6)
            sampled_users = random.sample(users, min(len(users), num_reviews))
            for u in sampled_users:
                rating = random.randint(1, 5)
                Review.objects.create(user=u, movie=movie, rating=rating,
                                      title=random.choice(["Amazing", "Good", "Okay", "Not Great", "Terrible"]),
                                      body=f"Auto-generated review with rating {rating}.")

        total_movies = Movie.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Seed complete. Total movies: {total_movies}. (user=testuser password=password123)'))
