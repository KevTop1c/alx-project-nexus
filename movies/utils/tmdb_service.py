import json
import logging
from datetime import datetime

import requests
from django.conf import settings
from django.core.cache import cache
from django_redis import get_redis_connection

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

            logger.info("Making TMDb API request to: %s", endpoint)
            response = requests.get(
                url, params=params, headers=self.headers, timeout=10
            )
            response.raise_for_status()
            logger.info(
                "TMDb API request successful: %s - Status: %s",
                endpoint,
                response.status_code,
            )
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
        Cache Key: trending_movies_{page}
        Cache Timeout: 1 hour
        """
        cache_key = f"trending_movies_{page}"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info(
                "✓ CACHE HIT: %s | Retrieved from Redis cache | Time: %s",
                cache_key,
                datetime.now().isoformat(),
            )
            return cached_data

        logger.info(
            "✗ CACHE MISSED: %s | Fetching from TMDb API | Time: %s",
            cache_key,
            datetime.now().isoformat(),
        )
        data = self._make_request("trending/movie/week", {"page": page})

        # Cache for 1 hour
        cache.set(cache_key, data, 3600)
        logger.info(
            "✓ CACHE SET: %s | Stored in Redis with TTL=3600s | Items: %s | Time: %s",
            cache_key,
            len(data.get("results", [])),
            datetime.now().isoformat(),
        )
        return data

    def get_recommended_movies(self, movie_id):
        """
        Fetch movie recommendations with Redis caching
        Cache Key: recommended_movies_{movie_id}
        Cache Timeout: 2 hours
        """
        cache_key = f"recommended_movies_{movie_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info(
                "✓ CACHE HIT: %s | Retrieved from Redis cache | Time: %s",
                cache_key,
                datetime.now().isoformat(),
            )
            return cached_data

        logger.info(
            "✗ CACHE MISSED: %s | Fetching from TMDb API | Time: %s",
            cache_key,
            datetime.now().isoformat(),
        )
        data = self._make_request(f"movie/{movie_id}/recommendations")

        # Cache for 2 hours
        cache.set(cache_key, data, 7200)
        logger.info(
            "✓ CACHE SET: %s | Stored in Redis with TTL=7200s | Items: %s | Time: %s",
            cache_key,
            len(data.get("results", [])),
            datetime.now().isoformat(),
        )
        return data

    def search_movies(self, query, page=1):
        """
        Search for movies by query
        """

        logger.info(
            "SEARCH REQUEST: query='%s' page=%s | Time: %s",
            query,
            page,
            datetime.now().isoformat(),
        )
        data = self._make_request("search/movie", {"query": query, "page": page})
        logger.info(
            "SEARCH COMPLETED: query='%s' | Results: %s | Time: %s",
            query,
            len(data.get("results", [])),
            datetime.now().isoformat(),
        )
        return data

    def get_movie_details(self, movie_id):
        """
        Get detailed information about a specific movie with caching
        """
        cache_key = f"movie_details_{movie_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info(
                "✓ CACHE HIT: %s | Retrieved from Redis cache | Time: %s",
                cache_key,
                datetime.now().isoformat(),
            )
            return cached_data

        logger.info(
            "✗ CACHE MISSED: %s | Fetching from TMDb API | Time: %s",
            cache_key,
            datetime.now().isoformat(),
        )
        data = self._make_request(f"movie/{movie_id}")

        # Cache for 24 hours (movie details rarely change)
        cache.set(cache_key, data, 86400)
        logger.info(
            "✓ CACHE SET: %s | Stored in Redis with TTL=86400s | Title: %s | Time: %s",
            cache_key,
            data.get("title", "N/A"),
            datetime.now().isoformat(),
        )
        return data

    def get_cache_stats(self):
        """
        Get cache statistics (useful for monitoring)
        """
        try:
            redis_conn = get_redis_connection("default")

            info = redis_conn.info("stats")
            stats = {
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": 0,
            }

            total_requests = stats["keyspace_hits"] + stats["keyspace_misses"]
            if total_requests > 0:
                stats["hit_rate"] = (stats["keyspace_hits"] / total_requests) * 100

            logger.info(
                "CACHE STATS: Hits=%s | Misses=%s | Hit Rate=%.2f%%",
                stats["keyspace_hits"],
                stats["keyspace_misses"],
                stats["hit_rate"],
            )
            return stats
        except Exception as e:
            logger.error("Failed to get cache stats: %s", e)
            return None
