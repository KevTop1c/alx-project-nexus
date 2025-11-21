import json
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import FavoriteMovie
from .utils.tmdb_service import TMDbService


class TMDbServiceTests(TestCase):
    """
    Test suite for TMDb API integration
    """

    def setUp(self):
        """Set up test fixtures"""
        self.tmdb_service = TMDbService()
        self.sample_movie_data = {
            "results": [
                {
                    "id": 550,
                    "title": "Fight Club",
                    "overview": "A test movie",
                    "poster_path": "/poster.jpg",
                    "backdrop_path": "/backdrop.jpg",
                    "release_date": "1999-10-15",
                    "vote_average": 8.4,
                    "vote_count": 26000,
                    "popularity": 85.5,
                }
            ],
            "page": 1,
            "total_pages": 100,
            "total_results": 2000,
        }
        cache.clear()

    def tearDown(self):
        """Clean up after tests"""
        cache.clear()

    @patch("requests.get")
    def test_get_trending_movies_success(self, mock_get):
        """Test successful trending movies API call"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_movie_data
        mock_get.return_value = mock_response

        result = self.tmdb_service.get_trending_movies(page=1)

        self.assertEqual(result["results"][0]["title"], "Fight Club")
        self.assertEqual(len(result["results"]), 1)
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_trending_movies_caching(self, mock_get):
        """Test that trending movies are cached correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_movie_data
        mock_get.return_value = mock_response

        # First call - should hit API
        result1 = self.tmdb_service.get_trending_movies(page=1)
        self.assertEqual(mock_get.call_count, 1)

        # Second call - should hit cache
        result2 = self.tmdb_service.get_trending_movies(page=1)
        self.assertEqual(mock_get.call_count, 1)  # Still 1, not called again

        # Results should be identical
        self.assertEqual(result1, result2)

        # Verify cache key exists
        cache_key = "trending_movies_1"
        cached_value = cache.get(cache_key)
        self.assertIsNotNone(cached_value)

    @patch("requests.get")
    def test_get_recommended_movies_success(self, mock_get):
        """Test successful recommended movies API call"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_movie_data
        mock_get.return_value = mock_response

        result = self.tmdb_service.get_recommended_movies(movie_id=550)

        self.assertEqual(result["results"][0]["title"], "Fight Club")
        self.assertEqual(len(result["results"]), 1)
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_recommended_movies_caching(self, mock_get):
        """Test that recommended movies are cached with 2-hour TTL"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_movie_data
        mock_get.return_value = mock_response

        # First call
        result1 = self.tmdb_service.get_recommended_movies(movie_id=550)

        # Second call - should hit cache
        result2 = self.tmdb_service.get_recommended_movies(movie_id=550)

        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(result1, result2)

    @patch("requests.get")
    def test_get_movie_details_success(self, mock_get):
        """Test successful movie details API call"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 550,
            "title": "Fight Club",
            "overview": "A detailed overview",
            "runtime": 139,
            "budget": 63000000,
            "revenue": 100000000,
        }
        mock_get.return_value = mock_response

        result = self.tmdb_service.get_movie_details(movie_id=550)

        self.assertEqual(result["title"], "Fight Club")
        self.assertEqual(result["runtime"], 139)

    @patch("requests.get")
    def test_get_movie_details_caching(self, mock_get):
        """Test that movie details are cached with 24-hour TTL"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 550, "title": "Fight Club"}
        mock_get.return_value = mock_response

        # First call
        result1 = self.tmdb_service.get_movie_details(movie_id=550)

        # Second call - should hit cache
        result2 = self.tmdb_service.get_movie_details(movie_id=550)

        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(result1, result2)

    @patch("requests.get")
    def test_search_movies_no_caching(self, mock_get):
        """Test that search results are not cached"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_movie_data
        mock_get.return_value = mock_response

        # First call
        self.tmdb_service.search_movies(query="Fight", page=1)

        # Second call
        self.tmdb_service.search_movies(query="Fight", page=1)

        # Should call API twice (no caching for search)
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.get")
    def test_api_request_failure(self, mock_get):
        """Test handling of API request failures"""
        mock_get.side_effect = Exception("Connection timeout")

        with self.assertRaises(Exception) as context:
            self.tmdb_service.get_trending_movies(page=1)

        self.assertIsInstance(context.exception, Exception)

    @patch("requests.get")
    def test_cache_different_pages(self, mock_get):
        """Test that different pages are cached separately"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_movie_data
        mock_get.return_value = mock_response

        # Get page 1
        self.tmdb_service.get_trending_movies(page=1)

        # Get page 2
        self.tmdb_service.get_trending_movies(page=2)

        # Should have called API twice for different pages
        self.assertEqual(mock_get.call_count, 2)

        # Verify both pages are cached
        self.assertIsNotNone(cache.get("trending_movies_1"))
        self.assertIsNotNone(cache.get("trending_movies_2"))


class MovieEndpointTests(APITestCase):
    """
    Test suite for movie API endpoints
    """

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        cache.clear()

    def tearDown(self):
        """Clean up after tests"""
        cache.clear()

    @patch("movies.views.tmdb_service.get_trending_movies")
    def test_trending_movies_endpoint(self, mock_trending):
        """Test trending movies endpoint returns data"""
        mock_trending.return_value = {
            "results": [{"id": 550, "title": "Fight Club"}],
            "page": 1,
        }

        url = reverse("trending-movies")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Fight Club")

    @patch("movies.views.tmdb_service.get_trending_movies")
    def test_trending_movies_with_pagination(self, mock_trending):
        """Test trending movies endpoint with page parameter"""
        mock_trending.return_value = {"results": [], "page": 2}

        url = reverse("trending-movies")
        response = self.client.get(url, {"page": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["page"], 2)

    @patch("movies.views.tmdb_service.get_recommended_movies")
    def test_recommended_movies_endpoint(self, mock_recommended):
        """Test recommended movies endpoint"""
        mock_recommended.return_value = {
            "results": [{"id": 551, "title": "Recommended Movie"}]
        }

        url = reverse("recommended-movies", kwargs={"movie_id": 550})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    @patch("movies.views.tmdb_service.search_movies")
    def test_search_movies_endpoint(self, mock_search):
        """Test search movies endpoint"""
        mock_search.return_value = {"results": [{"id": 550, "title": "Fight Club"}]}

        url = reverse("search-movies")
        response = self.client.get(url, {"query": "Fight"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_search_movies_without_query(self):
        """Test search endpoint returns error without query"""
        url = reverse("search-movies")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("movies.views.tmdb_service.get_movie_details")
    def test_movie_details_endpoint(self, mock_details):
        """Test movie details endpoint"""
        mock_details.return_value = {"id": 550, "title": "Fight Club", "runtime": 139}

        url = reverse("movie-details", kwargs={"movie_id": 550})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Fight Club")

    @patch("movies.views.tmdb_service.get_trending_movies")
    def test_endpoint_error_handling(self, mock_trending):
        """Test endpoint handles TMDb API errors gracefully"""
        mock_trending.side_effect = Exception("API Error")

        url = reverse("trending-movies")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)


class FavoriteMovieCRUDTests(APITestCase):
    """
    Test suite for favorite movies CRUD operations
    """

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )

        # Create sample favorite
        self.favorite = FavoriteMovie.objects.create(
            user=self.user,
            movie_id=550,
            title="Fight Club",
            poster_path="/poster.jpg",
            overview="Great movie",
            release_date="1999-10-15",
            vote_average=8.4,
        )

    def test_list_favorites_requires_authentication(self):
        """Test that listing favorites requires authentication"""
        url = reverse("favorite-movies")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_user_favorites(self):
        """Test listing user's favorite movies"""
        self.client.force_authenticate(user=self.user)

        url = reverse("favorite-movies")
        response = self.client.get(url)

        # the fix
        favorites = response.data.get("results", response.data)
        count = len(favorites)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(count, 1)
        self.assertEqual(favorites[0]["movie_id"], 550)
        self.assertEqual(favorites[0]["title"], "Fight Club")

    def test_list_favorites_only_shows_user_movies(self):
        """Test that users only see their own favorites"""
        # Create favorite for other user
        FavoriteMovie.objects.create(
            user=self.other_user, movie_id=551, title="Another Movie", vote_average=7.5
        )

        self.client.force_authenticate(user=self.user)

        url = reverse("favorite-movies")
        response = self.client.get(url)

        favorites = response.data.get("results", response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(favorites), 1)  # Only user's favorite
        self.assertEqual(favorites[0]["movie_id"], 550)

    def test_add_favorite_success(self):
        """Test adding a movie to favorites"""
        self.client.force_authenticate(user=self.user)

        url = reverse("add-favorite")
        data = {
            "movie_id": 551,
            "title": "The Matrix",
            "poster_path": "/matrix.jpg",
            "overview": "Sci-fi classic",
            "release_date": "1999-03-31",
            "vote_average": 8.7,
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FavoriteMovie.objects.filter(user=self.user).count(), 2)

        # Verify the favorite was created correctly
        favorite = FavoriteMovie.objects.get(user=self.user, movie_id=551)
        self.assertEqual(favorite.title, "The Matrix")
        self.assertEqual(favorite.vote_average, 8.7)

    def test_add_favorite_requires_authentication(self):
        """Test that adding favorite requires authentication"""
        url = reverse("add-favorite")
        data = {"movie_id": 552, "title": "New Movie"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_duplicate_favorite(self):
        """Test that duplicate favorites are rejected"""
        self.client.force_authenticate(user=self.user)

        url = reverse("add-favorite")
        data = {"movie_id": 550, "title": "Fight Club"}  # Already exists
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already in favorites", response.data["error"])

    def test_add_favorite_missing_required_fields(self):
        """Test validation of required fields"""
        self.client.force_authenticate(user=self.user)

        url = reverse("add-favorite")
        data = {"movie_id": 552}  # Missing title
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_favorite_success(self):
        """Test removing a movie from favorites"""
        self.client.force_authenticate(user=self.user)

        url = reverse("remove-favorite", kwargs={"movie_id": 550})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(FavoriteMovie.objects.filter(user=self.user).count(), 0)

    def test_remove_favorite_requires_authentication(self):
        """Test that removing favorite requires authentication"""
        url = reverse("remove-favorite", kwargs={"movie_id": 550})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_remove_nonexistent_favorite(self):
        """Test removing a favorite that doesn't exist"""
        self.client.force_authenticate(user=self.user)

        url = reverse("remove-favorite", kwargs={"movie_id": 999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_other_user_favorite(self):
        """Test that users cannot remove other users' favorites"""
        self.client.force_authenticate(user=self.other_user)

        url = reverse("remove-favorite", kwargs={"movie_id": 550})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Verify original favorite still exists
        self.assertTrue(
            FavoriteMovie.objects.filter(user=self.user, movie_id=550).exists()
        )

    def test_favorite_ordering(self):
        """Test that favorites are ordered by added_at descending"""
        self.client.force_authenticate(user=self.user)

        # Add another favorite
        FavoriteMovie.objects.create(
            user=self.user, movie_id=551, title="Newer Movie", vote_average=7.5
        )

        url = reverse("favorite-movies")
        response = self.client.get(url)

        favorites = response.data.get("results", response.data)  # the fix

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Newer favorite should be first
        self.assertEqual(favorites[0]["movie_id"], 551)
        self.assertEqual(favorites[1]["movie_id"], 550)


class CacheBehaviorTests(TestCase):
    """
    Test suite for caching behavior
    """

    def setUp(self):
        """Set up test fixtures"""
        cache.clear()
        self.tmdb_service = TMDbService()

    def tearDown(self):
        """Clean up after tests"""
        cache.clear()

    def test_cache_key_generation(self):
        """Test that cache keys are generated correctly"""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            mock_get.return_value = mock_response

            self.tmdb_service.get_trending_movies(page=1)
            self.assertIsNotNone(cache.get("trending_movies_1"))

            self.tmdb_service.get_movie_details(movie_id=550)
            self.assertIsNotNone(cache.get("movie_details_550"))

    def test_cache_ttl_different_endpoints(self):
        """Test that different endpoints have different TTLs"""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            mock_get.return_value = mock_response

            # Trending: 1 hour (3600s)
            self.tmdb_service.get_trending_movies(page=1)

            # Recommendations: 2 hours (7200s)
            self.tmdb_service.get_recommended_movies(movie_id=550)

            # Details: 24 hours (86400s)
            self.tmdb_service.get_movie_details(movie_id=550)

            # Verify all are cached
            self.assertIsNotNone(cache.get("trending_movies_1"))
            self.assertIsNotNone(cache.get("recommended_movies_550"))
            self.assertIsNotNone(cache.get("movie_details_550"))

    def test_cache_invalidation(self):
        """Test manual cache invalidation"""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            mock_get.return_value = mock_response

            # Cache data
            self.tmdb_service.get_trending_movies(page=1)
            self.assertIsNotNone(cache.get("trending_movies_1"))

            # Invalidate cache
            cache.delete("trending_movies_1")
            self.assertIsNone(cache.get("trending_movies_1"))

    def test_cache_isolation_between_pages(self):
        """Test that different pages don't interfere with each other"""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": [], "page": 1}
            mock_get.return_value = mock_response

            # Cache page 1
            result1 = self.tmdb_service.get_trending_movies(page=1)

            # Modify response for page 2
            mock_response.json.return_value = {"results": [], "page": 2}
            result2 = self.tmdb_service.get_trending_movies(page=2)

            # Verify both are cached separately
            cached1 = cache.get("trending_movies_1")
            cached2 = cache.get("trending_movies_2")

            self.assertIsNotNone(cached1)
            self.assertIsNotNone(cached2)
            self.assertNotEqual(cached1, cached2)
