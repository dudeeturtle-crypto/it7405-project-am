import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import django
from django.test import Client
import pprint

# Ensure project settings are used
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviereviews.settings')
django.setup()

client = Client()
urls = ['/', '/movies/another-movie/']
IMAGE_URL = 'https://d3tvwjfge35btc.cloudfront.net/Assets/11/824/L_p0027482411.jpg'

for u in urls:
    print('\nREQUEST ->', u)
    resp = client.get(u)
    print('Status code:', resp.status_code)
    html = resp.content.decode('utf-8', 'ignore')
    print('HTML length:', len(html))
    contains_image = IMAGE_URL in html
    print('Contains image URL:', contains_image)
    # show small snippet around first <img> if present
    img_idx = html.find('<img')
    if img_idx != -1:
        snippet = html[img_idx:img_idx+400]
        print('\nFirst <img> snippet:\n', snippet)
    else:
        # show snippet around movie title 'Another'
        t_idx = html.find('Another')
        if t_idx != -1:
            print('\nSnippet around "Another":\n', html[t_idx-80:t_idx+120])
        else:
            print('\nCould not find <img> or title snippet; printing first 400 chars:\n', html[:400])

print('\nDone')
