import os
from functools import lru_cache
from pymongo import MongoClient

# Reads connection info from environment variables. Default is localhost.
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_NAME = os.getenv('MONGODB_NAME', 'moviereviews_db')
# Allow a toggle to disable Mongo usage; default is False.
USE_MONGODB = os.getenv('USE_MONGODB', 'False') == 'True'


@lru_cache(maxsize=1)
def get_client():
    """Return a cached MongoClient instance or None if Mongo is disabled.

    This function is safe to import even if Mongo is not enabled. Callers
    should check for a None return and handle it (fall back to SQL or skip
    Mongo behaviour).
    """
    if not USE_MONGODB:
        return None
    # You can pass ssl/tls params here if you use Atlas with TLS
    return MongoClient(MONGODB_URI)


def get_db():
    """Return the selected database object or None if Mongo is disabled."""
    client = get_client()
    if client is None:
        return None
    return client[MONGODB_NAME]
