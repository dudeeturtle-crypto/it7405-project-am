import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from accounts.mongo_connection import get_db
import pprint

db = get_db()
if db is None:
    print('MongoDB not available')
else:
    before = db.movies.find_one({'slug': 'another-movie'}, {'_id': 0})
    print('before:')
    pprint.pprint(before)
    db.movies.update_one({'slug': 'another-movie'}, {'$set': {'title': 'Another'}})
    after = db.movies.find_one({'slug': 'another-movie'}, {'_id': 0})
    print('\nafter:')
    pprint.pprint(after)
