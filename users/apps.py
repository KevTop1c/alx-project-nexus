import logging
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        # Import signals only after app registry is ready
        try:
            import users.signals
        except ImportError:
            # Log error but don't crash the app
            logging.getLogger(__name__).warning("Failed to import users signals")
