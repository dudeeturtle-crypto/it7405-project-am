from accounts.mongo_connection import get_db

db = get_db()
if db is None:
    print('MongoDB not enabled or connection failed')
else:
    print('Before:', db.movies.find_one({'slug': 'example-movie'}).get('title'))
    db.movies.update_one({'slug': 'example-movie'}, {'$set': {'title': 'Rush Hour'}})
    print('After:', db.movies.find_one({'slug': 'example-movie'}).get('title'))
