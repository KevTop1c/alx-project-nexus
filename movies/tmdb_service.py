import logging
import json
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class TMDbService:
    """
    Service class for interacting with The Movie Database (TMDb) API
    """

    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        self.base_url = settings.TMDB_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json;charset=utf-8",
        }

    def _make_request(self, endpoint, params=None):
        """
        Make HTTP request to TMDb API with error handling
        """
        try:
            url = f"{self.base_url}/{endpoint}"
            params = params or {}
            params["api_key"] = self.api_key

            response = requests.get(
                url, params=params, headers=self.headers, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error while fetching TMDb data: %s", e)
            raise
        except requests.exceptions.Timeout:
            logger.error("TMDb API request timed out")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error: %s", e)
            raise
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON response from TMDb: %s", e)
            raise ValueError("TMDb returned invalid JSON") from e
        except requests.exceptions.RequestException as e:
            logger.error("Unexpected TMDb request failure: %s", e)
            raise RuntimeError("Failed to fetch data from TMDb") from e

    def get_trending_movies(self, page=1):
        """
        Fetch trending movies with Redis caching
        Cache key: trending_movies_{page}
        Cache timeout: 1 hour
        """
        cache_key = f"trending_movies_{page}"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info("Cache hit for %s", cache_key)
            return cached_data

        logger.info("Cache miss for %s, fetching from TMDb", cache_key)
        data = self._make_request("trending/movie/week", {"page": page})

        # Cache for 1 hour
        cache.set(cache_key, data, 3600)
        return data

    def get_recommended_movies(self, movie_id):
        """
        Fetch movie recommendations with Redis caching
        Cache key: recommended_movies_{movie_id}
        Cache timeout: 2 hours
        """
        cache_key = f"recommended_movies_{movie_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info("Cache hit for %s", cache_key)
            return cached_data

        logger.info("Cache miss for %s, fetching from TMDb", cache_key)
        data = self._make_request(f"movie/{movie_id}/recommendations")

        # Cache for 2 hours
        cache.set(cache_key, data, 7200)
        return data

    def search_movies(self, query, page=1):
        """
        Search for movies by query
        """
        return self._make_request("search/movie", {"query": query, "page": page})

    def get_movie_details(self, movie_id):
        """
        Get detailed information about a specific movie with caching
        """
        cache_key = f"movie_details_{movie_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info("Cache hit for {%s", cache_key)
            return cached_data

        logger.info("Cache miss for %s, fetching from TMDb", cache_key)
        data = self._make_request(f"movie/{movie_id}")

        # Cache for 24 hours (movie details rarely change)
        cache.set(cache_key, data, 86400)
        return data
