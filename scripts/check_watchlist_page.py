from django.test import Client
from django.contrib.auth.models import User

# Get or create test user
user = User.objects.get_or_create(username='testuser', defaults={'email': 'test@example.com'})[0]

client = Client()

# Test 1: Unauthenticated user trying to access watchlist
print("Test 1: Unauthenticated user accessing watchlist")
resp = client.get('/movies/watchlist/')
print(f"  Status: {resp.status_code}")
print(f"  Redirects to login: {resp.status_code == 302 or 'login' in resp.url if hasattr(resp, 'url') else 'N/A'}")

# Test 2: Authenticated user accessing watchlist
print("\nTest 2: Authenticated user accessing watchlist")
client.force_login(user)
resp = client.get('/movies/watchlist/')
print(f"  Status: {resp.status_code}")
if resp.status_code == 200:
    text = resp.content.decode('utf-8', errors='ignore')
    print(f"  Contains 'watchlist': {'watchlist' in text.lower()}")
    print(f"  Contains 'My Watchlist': {'My Watchlist' in text}")
    print(f"  SUCCESS: Watchlist page loads correctly!")
else:
    print(f"  ERROR: Got status {resp.status_code}")
    if hasattr(resp, 'url'):
        print(f"  Redirected to: {resp.url}")
