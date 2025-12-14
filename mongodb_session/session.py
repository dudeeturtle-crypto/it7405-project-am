import pymongo
from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase, CreateError
from django.utils import timezone
import datetime

class SessionStore(SessionBase):
    """A MongoDB-based session store."""
    def __init__(self, session_key=None):
        super().__init__(session_key)
        self.client = pymongo.MongoClient(settings.MONGODB_URI or 'mongodb://localhost:27017')
        self.db = self.client[settings.MONGODB_NAME]
        self.collection = self.db['django_sessions']

    def load(self):
        session = self.collection.find_one({'_id': self.session_key})
        now = timezone.now()
        expire_date = session.get('expire_date') if session else None
        # Ensure expire_date is always aware
        if expire_date and isinstance(expire_date, datetime.datetime):
            if expire_date.tzinfo is None:
                expire_date = expire_date.replace(tzinfo=datetime.timezone.utc)
        if session and expire_date and expire_date > now:
            return self.decode(session['session_data'])
        self.create()
        return {}

    def create(self):
        while True:
            self._session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            return

    def save(self, must_create=False):
        key = self._get_or_create_session_key()
        session_data = self.encode(self._get_session(no_load=must_create))
        expire_date = self.get_expiry_date()
        # Ensure expire_date is always aware
        if expire_date.tzinfo is None:
            expire_date = expire_date.replace(tzinfo=datetime.timezone.utc)
        doc = {
            '_id': key,
            'session_data': session_data,
            'expire_date': expire_date,
        }
        if must_create:
            if self.collection.find_one({'_id': key}):
                raise CreateError
            self.collection.insert_one(doc)
        else:
            self.collection.update_one({'_id': key}, {'$set': doc}, upsert=True)

    def exists(self, session_key):
        return self.collection.find_one({'_id': session_key}) is not None

    def delete(self, session_key=None):
        key = session_key or self.session_key
        self.collection.delete_one({'_id': key})

    @classmethod
    def clear_expired(cls):
        client = pymongo.MongoClient(settings.MONGODB_URI or 'mongodb://localhost:27017')
        db = client[settings.MONGODB_NAME]
        db['django_sessions'].delete_many({'expire_date': {'$lt': timezone.now()}})
