from django.test import Client
from django.contrib.auth.models import User

user = User.objects.get_or_create(username='testuser', defaults={'email': 'test@example.com'})[0]

client = Client()
client.force_login(user)

# Test different URL patterns
urls_to_test = [
    '/watchlist/',
    '/movies/watchlist/',
    '/movies',
]

print("Testing watchlist URL patterns:")
for url in urls_to_test:
    resp = client.get(url)
    print(f"  GET {url} -> {resp.status_code}")
