from accounts.mongo_connection import get_db

TARGET_SLUG = 'example-movie'
NEW_RATING = 4.9

db = get_db()
if db is None:
    print('MongoDB not enabled or connection failed')
else:
    # Update movie avg_rating
    movie = db.movies.find_one({'slug': TARGET_SLUG})
    if not movie:
        print('No movie document found for', TARGET_SLUG)
    else:
        print('Before movie avg_rating:', movie.get('avg_rating'))
        db.movies.update_one({'slug': TARGET_SLUG}, {'$set': {'avg_rating': NEW_RATING}})
        print('After movie avg_rating:', db.movies.find_one({'slug': TARGET_SLUG}).get('avg_rating'))

    # Update seed reviews for that movie (seed_user)
    res = db.reviews.update_many({'movie_slug': TARGET_SLUG, 'user': 'seed_user'}, {'$set': {'rating': NEW_RATING}})
    print('Updated review documents matched/modified:', res.matched_count, res.modified_count)

    # Show one review for confirmation
    doc = db.reviews.find_one({'movie_slug': TARGET_SLUG})
    if doc:
        print('Sample review now:', {'title': doc.get('title'), 'rating': doc.get('rating'), 'user': doc.get('user')})
    else:
        print('No reviews found for', TARGET_SLUG)
