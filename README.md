# Movie Reviews (Django + MongoDB)

This is a production-style movie review website built with Django and MongoDB.

Tech stack
- Backend: Django (Python 3)
- Database: MongoDB (via `djongo`)
- Frontend: Django templates + Bootstrap

Quick start

1. Create and activate a virtual environment

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Set environment variables (create a `.env` file at project root)

Example `.env`:

```
DEBUG=True
SECRET_KEY=change-me-in-prod
MONGODB_URI=mongodb://localhost:27017/moviereviews_db
```

4. Run migrations (djongo uses Django migrations)

```powershell
python manage.py migrate
```

5. Load sample data

```powershell
python manage.py seed_data
```

6. Run server

```powershell
python manage.py runserver
```

Default test user
- username: `testuser` (created by seed)
- password: `password123`

## Architecture Update: MongoDB for Movies App

The `movies` app has been migrated to use MongoDB exclusively:

### What Changed
- **Movies models**: Removed SQL `Movie` and `Review` models from Django ORM
- **Database**: All movie and review data stored in MongoDB collections
- **Forms**: Converted to plain Django Forms instead of ModelForms
- **Views**: Updated to use MongoDB helpers (`movies/mongo_access.py`)
- **Tests**: Modified to use MongoDB directly

### Data Storage
- **SQLite**: Django admin, sessions, authentication (accounts app)
- **MongoDB**: Movies (18 documents), Reviews (9+ documents), Users (3+ documents)

### Collections
```
moviereviews_db
├── movies       # Movie documents with title, year, rating, poster_url, etc.
├── reviews      # Review documents with user_id, movie_id, rating, text
└── users        # User accounts (username, email, hashed password)
```

### Commands
```powershell
# Seed MongoDB with movie data from JSON
python manage.py import_movies_json

# Seed sample reviews
python manage.py seed_mongo

# Run tests (uses in-memory SQLite, MongoDB tests use production DB)
python manage.py test movies accounts
```

### Reverting to SQL (if needed)
If you need to use SQL for the movies app:
1. Restore `movies/models.py` with SQL model definitions
2. Create and apply migrations: `python manage.py makemigrations && python manage.py migrate`
3. Convert forms back to ModelForms
4. Update views to use Django ORM (`Movie.objects.all()` etc.)
5. Authentication (accounts app) can remain as hybrid SQL/MongoDB

### Notes
- Set `MONGODB_URI` to your MongoDB connection string. When using MongoDB Atlas, include credentials and replica set parameters as required.
- Uses `pymongo` for direct MongoDB access (no ORM layer)
- Password hashing uses PBKDF2 with 100,000 iterations
