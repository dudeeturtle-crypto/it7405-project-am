"""Check where signups/logins are stored: Mongo `users` vs SQLite `auth_user`/sessions.

Run this with the project's venv Python. The script prints counts and samples.
"""
from pprint import pprint
import sqlite3
import sys

def mongo_check():
    try:
        import scripts.mongo_tools as mt
        db = mt.get_db_or_raise()
        users_count = db['users'].count_documents({})
        sample_users = list(db['users'].find({}, {'_id':0}).limit(10))
        print('MONGO OK')
        print('users_count:', users_count)
        print('sample_users:')
        pprint(sample_users)
    except Exception as e:
        print('MONGO ERROR:', e)


def sqlite_check(sqlite_path='db.sqlite3'):
    try:
        conn = sqlite3.connect(sqlite_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print('\nSQLITE OK')
        print('tables:', tables)
        auth_tables = [t for t in tables if 'auth' in t or 'user' in t or 'session' in t]
        print('auth/session-like tables:', auth_tables)
        if 'auth_user' in tables:
            cur.execute('SELECT id, username, email FROM auth_user LIMIT 10')
            print('auth_user rows:', cur.fetchall())
        if 'django_session' in tables:
            cur.execute('SELECT session_key, expire_date FROM django_session LIMIT 10')
            print('django_session rows:', cur.fetchall())
        conn.close()
    except Exception as e:
        print('SQLITE ERROR:', e)


def main():
    print('Running storage checks...')
    mongo_check()
    sqlite_check()


if __name__ == '__main__':
    main()
