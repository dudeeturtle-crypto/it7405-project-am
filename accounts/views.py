from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import SignUpForm, LoginForm
from .mongo_users import (
    create_user, authenticate_user, get_user_by_email,
    user_exists, username_exists
)


@require_http_methods(["GET", "POST"])
def signup_view(request):
    """Handle user signup with MongoDB"""
    if request.user.is_authenticated:
        return redirect('movies:home')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Check if user already exists
            if user_exists(email):
                messages.error(request, 'Email already registered. Please log in or use a different email.')
                return render(request, 'accounts/signup.html', {'form': form})
            
            if username_exists(username):
                messages.error(request, 'Username already taken. Please choose a different username.')
                return render(request, 'accounts/signup.html', {'form': form})
            
            try:
                user_id = create_user(username, email, password)
                if user_id:
                    messages.success(request, 'Account created successfully! Please log in.')
                    return redirect('accounts:login')
                else:
                    messages.error(request, 'Failed to create account. Please try again.')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
                return render(request, 'accounts/signup.html', {'form': form})
    else:
        form = SignUpForm()
    
    return render(request, 'accounts/signup.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Handle user login with MongoDB"""
    if request.user.is_authenticated:
        return redirect('movies:home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            user = authenticate_user(email, password)
            if user:
                # Set session for user
                request.session['user_id'] = str(user['_id'])
                request.session['username'] = user['username']
                request.session['email'] = user['email']
                messages.success(request, f'Welcome back, {user["username"]}!')
                return redirect('movies:home')
            else:
                messages.error(request, 'Invalid email or password.')
                return render(request, 'accounts/login.html', {'form': form})
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(["GET"])
def logout_view(request):
    """Handle user logout"""
    # Clear session
    if 'user_id' in request.session:
        del request.session['user_id']
    if 'username' in request.session:
        del request.session['username']
    if 'email' in request.session:
        del request.session['email']
    
    messages.success(request, 'You have been logged out.')
    return redirect('movies:home')


@require_http_methods(["GET"])
def profile_view(request):
    """Display user profile"""
    if not request.session.get('user_id'):
        messages.warning(request, 'Please log in to view your profile.')
        return redirect('accounts:login')
    
    user_id = request.session.get('user_id')
    user = get_user_by_email(request.session.get('email'))
    
    if not user:
        messages.error(request, 'User not found.')
        return redirect('accounts:login')
    
    return render(request, 'accounts/profile.html', {'user': user})


@require_http_methods(["GET", "POST"])
def admin_login_view(request):
    """Dedicated admin login page"""
    if request.session.get('username'):
        # User already logged in, redirect to home or admin dashboard
        from accounts.mongo_connection import get_db
        db = get_db()
        username = request.session.get('username')
        try:
            user = db.users.find_one({'username': username})
            if user and user.get('is_admin'):
                return redirect('movies:admin_dashboard')
        except Exception:
            pass
        return redirect('movies:home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'accounts/admin_login.html')
        
        # Authenticate admin user
        from accounts.mongo_connection import get_db
        db = get_db()
        
        try:
            user = db.users.find_one({'username': username})
            if user and user.get('password') == password and user.get('is_admin'):
                # Set session for admin
                request.session['user_id'] = str(user['_id'])
                request.session['username'] = user['username']
                request.session['email'] = user['email']
                messages.success(request, f'Welcome, Admin {username}!')
                return redirect('movies:admin_dashboard')
            else:
                messages.error(request, 'Invalid admin credentials.')
                return render(request, 'accounts/admin_login.html')
        except Exception as e:
            messages.error(request, f'Login error: {str(e)}')
            return render(request, 'accounts/admin_login.html')
    
    return render(request, 'accounts/admin_login.html')
