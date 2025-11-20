import logging
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        # Import signals only after app registry is ready
        try:
            import users.signals
        except ImportError as e:
            # Log error but don't crash the app
            logging.getLogger(__name__).warning("Failed to import users signals %s", e)

        # Backfill profiles for users who have no profile
        try:
            from django.contrib.auth import get_user_model
            from users.models import Profile

            User = get_user_model()

            for user in User.objects.all():
                Profile.objects.get_or_create(user=user)

        except Exception as e:
            logging.getLogger(__name__).warning("Failed to backfill profiles: %s", e)
