from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from .tasks import fetch_movie_details_async, refresh_trending_cache, send_favorite_notification

User = get_user_model()
TEST_PASSWORD = "testpass123"  # nosec B105,B106


class CeleryTaskTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password=TEST_PASSWORD)

    @patch("movies.tasks.tmdb_service.get_trending_movies")
    def test_refresh_trending_cache(self, mock_trending):
        mock_trending.return_value = {"results": []}

        result = refresh_trending_cache()

        self.assertEqual(result["status"], "success")
        self.assertEqual(mock_trending.call_count, 3)

    @patch("movies.tasks.send_mail")
    def test_send_favorite_notification(self, mock_mail):
        result = send_favorite_notification(user_id=self.user.id, movie_title="Test Movie")

        self.assertEqual(result["status"], "success")
        mock_mail.assert_called_once()

    @patch("movies.tasks.tmdb_service.get_movie_details")
    def test_fetch_movie_details_async(self, mock_details):
        mock_details.return_value = {"id": 550, "title": "Fight Club"}

        result = fetch_movie_details_async(movie_id=550)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["movie_id"], 550)
