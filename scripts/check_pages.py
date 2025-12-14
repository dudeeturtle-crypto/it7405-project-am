import urllib.request
import time

urls = [
    'http://127.0.0.1:8001/',
    'http://127.0.0.1:8001/movies/another-movie/'
]
IMAGE_URL = 'https://d3tvwjfge35btc.cloudfront.net/Assets/11/824/L_p0027482411.jpg'

for u in urls:
    ok = False
    for i in range(12):
        try:
            r = urllib.request.urlopen(u, timeout=2)
            html = r.read().decode('utf-8', 'ignore')
            print(f'URL: {u} -> HTTP {r.getcode()}, length={len(html)}')
            print('Contains image URL:', IMAGE_URL in html)
            # try to find <img> snippet
            idx = html.find('<img')
            if idx != -1:
                snippet = html[idx:idx+400]
                print('First <img> snippet:\n', snippet)
            else:
                # try to find title
                t = html.find('Another')
                if t != -1:
                    print('Found title "Another" at index', t)
                    print('HTML around title:\n', html[t-80:t+120])
            ok = True
            break
        except Exception as e:
            time.sleep(0.5)
    if not ok:
        print(f'ERROR: Could not fetch {u}')

print('Done')
