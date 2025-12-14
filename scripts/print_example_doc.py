from accounts.mongo_connection import get_db

db = get_db()
if db is None:
    print('MongoDB not enabled or connection failed')
else:
    doc = db.movies.find_one({'slug': 'example-movie'})
    print(doc)
