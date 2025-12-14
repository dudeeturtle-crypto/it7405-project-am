from django.db import migrations


class Migration(migrations.Migration):
    """No-op migration: the `movies` app stores data in MongoDB and does not
    require SQL table creation. This migration is intentionally empty to avoid
    Django attempting to create the old Movie/Review tables.
    """

    initial = True

    dependencies = []

    operations = []
