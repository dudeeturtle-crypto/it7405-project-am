from django.core.management.base import BaseCommand
from accounts.mongo_connection import get_db
from django.utils import timezone


class Command(BaseCommand):
    help = 'Create an admin user account'

    def handle(self, *args, **options):
        db = get_db()
        if db is None:
            self.stdout.write(self.style.ERROR('MongoDB not connected'))
            return

        # Admin credentials
        username = 'admin'
        email = 'admin@moviereviews.com'
        password = 'admin123'  # Development credentials
        
        # Check if admin already exists
        existing_admin = db.users.find_one({'username': username})
        if existing_admin:
            self.stdout.write(self.style.WARNING(f'Admin user "{username}" already exists'))
            return

        # Create admin user
        admin_user = {
            'username': username,
            'email': email,
            'password': password,
            'is_admin': True,
            'created_at': timezone.now().isoformat(),
        }
        
        result = db.users.insert_one(admin_user)
        
        if result.inserted_id:
            self.stdout.write(self.style.SUCCESS('✓ Admin user created successfully'))
            self.stdout.write(self.style.SUCCESS(f'  Username: {username}'))
            self.stdout.write(self.style.SUCCESS(f'  Password: {password}'))
            self.stdout.write(self.style.SUCCESS(f'  Email: {email}'))
            self.stdout.write(self.style.WARNING('  WARNING: Change this password in production!'))
        else:
            self.stdout.write(self.style.ERROR('Failed to create admin user'))
