"""
Test RabbitMQ connection and queue tasks
Usage: python manage.py test_rabbitmq
"""

from django.core.management.base import BaseCommand
from movies.tasks import (
    send_favorite_notification,
    fetch_movie_details_async,
    refresh_trending_cache,
)
import time


class Command(BaseCommand):
    help = "Test RabbitMQ connection and task queueing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--task", type=str, help="Specific task to test", default=""
        )

    def handle(self, *args, **options):
        task_name = options["task"]

        self.stdout.write(self.style.SUCCESS("=== Testing RabbitMQ ==="))

        try:
            if task_name == "notification":
                self.test_notification_task()
            elif task_name == "cache":
                self.test_cache_task()
            elif task_name == "api":
                self.test_api_task()
            else:
                self.test_all_queues()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error: {str(e)}"))
            raise

    def test_notification_task(self):
        """Test email queue"""
        self.stdout.write("\n--- Testing Email Queue ---")

        from django.contrib.auth.models import User

        user = User.objects.filter(email__isnull=False).exclude(email="").first()

        if not user:
            self.stdout.write(self.style.WARNING("No user with email found"))
            return

        result = send_favorite_notification.delay(
            user_id=user.id, movie_title="Test Movie from RabbitMQ"
        )

        self.stdout.write(f"Task ID: {result.id}")
        self.stdout.write(f"Queue: emails")
        self.stdout.write(f"User: {user.username}")

    def test_cache_task(self):
        """Test cache queue"""
        self.stdout.write("\n--- Testing Cache Queue ---")

        result = refresh_trending_cache.delay()

        self.stdout.write(f"Task ID: {result.id}")
        self.stdout.write(f"Queue: cache")

    def test_api_task(self):
        """Test API queue"""
        self.stdout.write("\n--- Testing API Queue ---")

        result = fetch_movie_details_async.delay(movie_id=550)

        self.stdout.write(f"Task ID: {result.id}")
        self.stdout.write(f"Queue: api")
        self.stdout.write(f"Movie ID: 550")

    def test_all_queues(self):
        """Test all queues"""
        self.stdout.write("\n--- Testing All Queues ---")

        self.test_cache_task()
        self.test_api_task()

        self.stdout.write(self.style.SUCCESS("\n✓ All queues tested!"))
