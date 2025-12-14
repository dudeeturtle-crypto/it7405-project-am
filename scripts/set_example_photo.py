import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from accounts.mongo_connection import get_db
import pprint

PHOTO = 'https://tse3.mm.bing.net/th/id/OIP.Jpxv8g05O-UJhQceYe3BuAHaKk?rs=1&pid=ImgDetMain&o=7&rm=3'

db = get_db()
if db is None:
    print('MongoDB not available')
else:
    before = db.movies.find_one({'slug': 'example-movie'}, {'_id': 0})
    print('before:')
    pprint.pprint(before)
    db.movies.update_one({'slug': 'example-movie'}, {'$set': {'photo_url': PHOTO}})
    after = db.movies.find_one({'slug': 'example-movie'}, {'_id': 0})
    print('\nafter:')
    pprint.pprint(after)
