from accounts.mongo_connection import get_db

TARGET_TITLE = 'Gladiator'
NEW_RATING = 4.7

db = get_db()
if db is None:
    print('MongoDB not enabled or connection failed')
else:
    # Try to find by title
    movie = db.movies.find_one({'title': TARGET_TITLE})
    if not movie:
        # Try common slug variant
        movie = db.movies.find_one({'slug': TARGET_TITLE.lower().replace(' ', '-')})
    if not movie:
        print('No movie document found for title/slug Gladiator')
    else:
        slug = movie.get('slug')
        print('Found movie:', movie.get('title'), 'slug=', slug)
        print('Before avg_rating:', movie.get('avg_rating'))
        db.movies.update_one({'_id': movie['_id']}, {'$set': {'avg_rating': NEW_RATING}})
        print('After avg_rating:', db.movies.find_one({'_id': movie['_id']}).get('avg_rating'))

        # Update reviews that reference this movie slug
        if slug:
            res = db.reviews.update_many({'movie_slug': slug}, {'$set': {'rating': NEW_RATING}})
            print('Updated review docs matched/modified:', res.matched_count, res.modified_count)
            sample = db.reviews.find_one({'movie_slug': slug})
            if sample:
                print('Sample review now:', {'title': sample.get('title'), 'rating': sample.get('rating'), 'user': sample.get('user')})
        else:
            print('Movie has no slug; skipping review updates')
