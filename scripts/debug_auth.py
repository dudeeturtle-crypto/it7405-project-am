from django.test import Client
from django.contrib.auth.models import User

user = User.objects.get_or_create(username='testuser', defaults={'email': 'test@example.com'})[0]

client = Client()
client.force_login(user)

# Fetch movie detail page
resp = client.get('/movies/gladiator/')
print(f"Status: {resp.status_code}")

# Check context
if resp.context:
    print(f"\nContext keys: {list(resp.context.keys())}")
    
    # Check user authentication
    if 'user' in resp.context:
        ctx_user = resp.context['user']
        print(f"\nUser in context:")
        print(f"  Username: {ctx_user.username if hasattr(ctx_user, 'username') else 'N/A'}")
        print(f"  is_authenticated: {ctx_user.is_authenticated if hasattr(ctx_user, 'is_authenticated') else 'N/A'}")
    
    # Check is_favorited
    if 'is_favorited' in resp.context:
        print(f"\nis_favorited in context: {resp.context['is_favorited']}")
    else:
        print(f"\nWARNING: is_favorited NOT in context")

# Check HTML
text = resp.content.decode('utf-8', errors='ignore')
print(f"\nHTML checks:")
print(f"  Contains 'Log in': {'Log in' in text}")
print(f"  Contains 'favorite-btn': {'favorite-btn' in text}")
print(f"  Contains '[LOVE]': {'[LOVE]' in text}")

if 'Log in' in text and 'favorite-btn' not in text:
    print(f"\nISSUE: Template is showing login message instead of button")
    print(f"This means user.is_authenticated is evaluating to False in the template")
