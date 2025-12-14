import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviereviews.settings')
django.setup()

from django.test import Client

def main():
    c = Client()
    try:
        r = c.get('/')
        print('STATUS', r.status_code)
        print('CONTENT_START')
        content = r.content.decode('utf-8', errors='replace')
        print(content[:8000])
        print('\nCONTENT_END')
    except Exception as e:
        import traceback
        print('EXCEPTION:')
        traceback.print_exc()

if __name__ == '__main__':
    main()
