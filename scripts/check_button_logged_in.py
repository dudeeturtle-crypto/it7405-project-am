from django.test import Client
from django.contrib.auth.models import User

# Create a test user
user, created = User.objects.get_or_create(username='testuser', defaults={'email': 'test@example.com'})

client = Client()

# Log in the test user
client.force_login(user)

# Test: Check if button appears when logged in
print("Test: Authenticated user (logged in)")
resp = client.get('/movies/gladiator/')
text = resp.content.decode('utf-8', errors='ignore')
has_button = 'favorite-btn' in text or 'Add to Watchlist' in text or 'Remove from Watchlist' in text
has_love = '[LOVE]' in text

print(f"  Status: {resp.status_code}")
print(f"  Contains favorite button: {has_button}")
print(f"  Contains [LOVE] text: {has_love}")

if has_button:
    # Find and print snippet
    idx = text.find('favorite-btn')
    if idx > -1:
        snippet = text[max(0, idx-100):idx+300]
        print(f"\n  Button HTML found:")
        print(f"  {snippet[:200]}")
        print(f"  ...")
else:
    print("  WARNING: Button still not found!")
    # Debug: check context
    if resp.context:
        print(f"  Context has is_favorited: {'is_favorited' in resp.context}")
        print(f"  user.is_authenticated: {resp.context.get('user').is_authenticated if 'user' in resp.context else 'N/A'}")
