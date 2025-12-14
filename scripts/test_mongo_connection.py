from dotenv import load_dotenv
import os
from pymongo import MongoClient, errors

load_dotenv()
uri = os.getenv('MONGODB_URI')
name = os.getenv('MONGODB_NAME', 'moviereviews_db')
print('MONGODB_URI=', uri)
print('MONGODB_NAME=', name)
if not uri:
    print('No MONGODB_URI set; aborting')
    raise SystemExit(2)

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    # ping server
    client.admin.command('ping')
    print('Ping successful')
    db = client[name]
    print('Collections in DB:', db.list_collection_names())
except errors.ServerSelectionTimeoutError as e:
    print('Connection timed out or refused:', e)
    raise SystemExit(3)
except Exception as e:
    print('Unexpected error:', e)
    raise
