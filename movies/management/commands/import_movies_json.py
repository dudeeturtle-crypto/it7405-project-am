import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

from accounts.mongo_connection import get_db


class Command(BaseCommand):
    help = 'Import movies from the top-level movies.json into MongoDB (upserts by slug)'

    def handle(self, *args, **options):
        db = get_db()
        if db is None:
            self.stdout.write(self.style.WARNING('MongoDB is not enabled (USE_MONGODB=False) or not available. Aborting.'))
            return

        base = Path(settings.BASE_DIR)
        json_path = base / 'movies.json'
        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f'Could not find {json_path}'))
            return

        try:
            data = json.loads(json_path.read_text(encoding='utf-8'))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'Failed to read/parse JSON: {exc}'))
            return

        movies_coll = db.movies
        inserted = 0
        updated = 0
        from movies.models import slugify_title
        from django.utils import timezone

        for item in data:
            title = item.get('title') or item.get('name')
            if not title:
                continue
            slug = item.get('slug') or slugify_title(title)
            doc = {
                'title': title,
                'slug': slug,
                'description': item.get('description', ''),
                'photo_url': item.get('photo_url') or item.get('poster_url') or item.get('image'),
                # treat provided rating as initial avg_rating
                'avg_rating': float(item.get('rating') or 0.0),
                'review_count': int(item.get('review_count') or 0),
                'created_at': item.get('created_at') or timezone.now().isoformat(),
                'source': 'movies.json'
            }

            res = movies_coll.update_one({'slug': slug}, {'$set': doc}, upsert=True)
            if getattr(res, 'upserted_id', None) is not None:
                inserted += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Import complete. Inserted: {inserted}, Updated: {updated}'))