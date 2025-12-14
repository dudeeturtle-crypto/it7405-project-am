from django.test import Client

client = Client()

# Test 1: Check if button appears on movie detail page (unauthenticated)
print("Test 1: Unauthenticated user")
resp = client.get('/movies/gladiator/')
text = resp.content.decode('utf-8', errors='ignore')
has_button = 'favorite-btn' in text or 'Add to Watchlist' in text
print(f"  Status: {resp.status_code}")
print(f"  Contains favorite button: {has_button}")
if not has_button:
    print(f"  Contains login message: {'Log in' in text}")

# Test 2: Check if button appears when logged in
print("\nTest 2: Simulating logged-in user")
# Note: Django test client can't easily simulate login without User object
# But we can check the context to see if is_favorited is passed
if resp.context:
    print(f"  Context keys: {list(resp.context.keys())}")
    if 'is_favorited' in resp.context:
        print(f"  is_favorited in context: {resp.context['is_favorited']}")
    else:
        print("  WARNING: is_favorited NOT in context - may not be passed to template")

# Test 3: Check HTML structure
print("\nTest 3: HTML snippet check")
if 'favorite-btn' in text:
    idx = text.find('favorite-btn')
    snippet = text[max(0, idx-100):idx+200]
    print(f"  Found button HTML:\n{snippet}")
else:
    print("  Button not found in HTML")
