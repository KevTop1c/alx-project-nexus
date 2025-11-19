from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from decouple import config


class Command(BaseCommand):
    """Create an admin user if none exists"""

    help = "Create an admin user if none exists"

    def handle(self, *args, **options):
        User = get_user_model()
        username = config("DJANGO_SUPERUSER_USERNAME")
        email = config("DJANGO_SUPERUSER_EMAIL")
        password = config("DJANGO_SUPERUSER_PASSWORD")

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(
                self.style.SUCCESS(f"Superuser '{username}' created successfully!")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Superuser '{username}' already exists. Skipping creation."
                )
            )
