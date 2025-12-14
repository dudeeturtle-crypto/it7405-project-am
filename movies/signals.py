"""Signals for the movies app.

When the app used Django ORM models, signals recalculated aggregates on
movie save/delete. The app now stores movie and review data in MongoDB, so the
ORM-based signal handlers are not used. Keep this module present but inert so
importing `movies.apps` remains safe.
"""
try:
    from django.db.models.signals import post_save, post_delete  # noqa: F401
    from django.dispatch import receiver  # noqa: F401
    # ORM models are no longer present; skip registering any receivers.
except Exception:
    pass
