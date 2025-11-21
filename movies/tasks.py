import logging
from datetime import datetime, timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Avg, Count, Q
from django_redis import get_redis_connection

from .models import FavoriteMovie
from .utils.tmdb_service import TMDbService

logger = get_task_logger(__name__)
tmdb_service = TMDbService()


@shared_task(
    bind=True,
    name="movies.tasks.refresh_trending_cache",
    max_retries=3,
    default_retry_delay=300,
    priority=7,
)
def refresh_trending_cache(self):
    """
    Periodic task to refresh trending movies cache
    Runs every hour to keep trending data fresh
    Queue: cache
    Priority: 7 (high)
    """
    try:
        logger.info("Starting Trending Movies cache refresh")

        # Refresh first 3 pages of trending movies
        for page in range(1, 4):
            cache_key = f"trending_movies_{page}"
            logger.info("Refreshing cache for %s", cache_key)

            # Fetch fresh data from TMDb
            data = tmdb_service.get_trending_movies(page=page)

            # Update cache with 1 hour TTL
            cache.set(cache_key, data, 3600)
            logger.info("Successfully refreshed %s", cache_key)

        logger.info("Trending Movies cache refresh completed")
        return {"status": "success", "pages_refreshed": 3}

    except Exception as e:
        logger.error("Error refreshing Trending Movies cache: %s", e)
        # Retry task after 5 minutes if it fails
        raise self.retry(exc=e, countdown=300, max_retries=3)


@shared_task(
    bind=True,
    name="movies.tasks.cleanup_old_cache",
    max_retries=2,
    default_retry_delay=600,
    priority=5,
)
def cleanup_old_cache(self):
    """
    Cleanup old cache entries daily
    Removes stale cache keys to free up Redis memory
    Queue: cache
    Priority: 5 (medium)
    """
    try:
        logger.info("Starting cache cleanup task")

        redis_conn = get_redis_connection("default")

        # Get all cache keys
        pattern = "movies_app:*"
        keys = redis_conn.keys(pattern)

        cleanup_count = 0
        for key in keys:
            # Check TTL - if expired or -1 (no expiry), delete
            ttl = redis_conn.ttl(key)
            if ttl == -2 or ttl == -1:
                redis_conn.delete(key)
                cleanup_count += 1

        logger.info("Cache cleanup completed: %s keys removed", cleanup_count)
        return {"status": "success", "keys_cleanup": cleanup_count}

    except Exception as e:
        logger.error("Error during cache cleanup: %s", e)
        raise self.retry(exc=e, countdown=600, max_retries=2)


@shared_task(
    bind=True,
    name="movies.tasks.send_weekly_recommendations",
    max_retries=2,
    default_retry_delay=1800,
    priority=6,
)
def send_weekly_recommendations(self):
    """
    Send weekly personalized movie recommendations to active users
    Analyzes user favorites and sends email recommendations
    Queue: emails
    Priority: 6 (medium-high)
    """
    try:
        logger.info("Starting Weekly Recommendations task")

        # Get active users who have favorites
        active_users = User.objects.filter(
            is_active=True,
            email__isnull=False,
            favorites_movies__isnull=False,
        ).distinct()

        emails_sent = 0

        for user in active_users:
            try:
                # Get user's favorite movies
                favorites = FavoriteMovie.objects.filter(user=user)[:5]

                if not favorites:
                    continue

                # Build recommendation email
                movie_list = "\n".join(
                    [f"- {fav.title} (Rating: {fav.vote_average})" for fav in favorites]
                )

                subject = f'Your Weekly Movie Recommendations - {datetime.now().strftime("%B %d, %Y")}'
                message = f"""
                            Hi {user.username}!

                            Based on your favorite movies, here are your top picks this week:

                            {movie_list}

                            Log in to discover more movies you'll love!

                            Best regards,
                            Movie Recommendation Team
                            """

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                emails_sent += 1
                logger.info(f"Sent recommendations to {user.email}")

            except Exception as user_error:
                logger.error("Error sending email to %s: %s", user.email, user_error)
                continue

        logger.info("Weekly Recommendations completed: %s emails sent", emails_sent)
        return {"status": "success", "emails_sent": emails_sent}

    except Exception as e:
        logger.error("Error in weekly recommendation task: %s", e)
        raise self.retry(exc=e, countdown=1800, max_retries=2)


@shared_task(
    bind=True,
    name="movies.tasks.fetch_movie_details_async",
    max_retries=3,
    default_retry_delay=120,
    priority=6,
)
def fetch_movie_details_async(self, movie_id):
    """
    Asynchronously fetch and cache movie details
    Used for background processing of movie data
    Queue: api
    Priority: 6 (medium-high)
    """
    try:
        logger.info("Fetch details for movie %s", movie_id)

        # Fetch from TMDb API
        details = tmdb_service.get_movie_details(movie_id)

        # Cache for 24 hours
        cache_key = f"movie_details_{movie_id}"
        cache.set(cache_key, details, 86400)

        logger.info("Successfully cached details for movie %s", movie_id)
        return {
            "status": "success",
            "movie_id": movie_id,
            "title": details.get("title"),
        }
    except Exception as e:
        logger.error("Error fetching movie details for %s: %s", movie_id, e)
        raise self.retry(exc=e, countdown=120, max_retries=3)


@shared_task(
    bind=True,
    name="movies.tasks.send_favorite_notification",
    max_retries=3,
    default_retry_delay=60,
    priority=9,
)
def send_favorite_notification(self, user_id, movie_title):
    """
    Send notification when user adds a movie to favorites
    Immediate notification task
    Queue: emails
    Priority: 9 (very high - immediate user action)
    """
    try:
        user = User.objects.get(id=user_id)

        if not user.email:
            logger.warning("User '%s' has no email address", user.username)
            return {"status": "skipped", "reason": "no_email"}

        subject = f"Added to Favorites: {movie_title}"
        message = f"""
                    Hi {user.username}!

                    You've added "{movie_title}" to your favorites!

                    We'll keep you updated with similar recommendations.

                    Best regards,
                    Movie Recommendation Team
                    """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info("Sent favorite movie notification to %s", user.email)
        return {"status": "success", "user": user.username}

    except User.DoesNotExist:
        logger.error("User %s not found", user_id)
        return {"status": "error", "reason": "user_not_found"}

    except Exception as e:
        logger.error("Error sending favorite movie notification: %s", e)
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(
    bind=True,
    name="movies.tasks.generate_analytics_report",
    max_retries=2,
    default_retry_delay=600,
    priority=4,
)
def generate_analytics_report(self):
    """
    Generate analytics report for admin dashboard
    Runs every 12 hours
    Queue: reports
    Priority: 4 (low-medium)
    """
    try:
        logger.info("Starting Analytics Report generation")

        # Calculate various metrics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        total_favorites = FavoriteMovie.objects.count()

        # Most favorited movies
        top_movies = (
            FavoriteMovie.objects.values("movie_id", "title")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # Average ratings
        avg_rating = FavoriteMovie.objects.aggregate(avg=Avg("vote_average"))["avg"]

        # Users with most favorites
        top_users = User.objects.annotate(fav_count=Count("favorite_movies")).order_by(
            "-fav_count"
        )[:10]

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_users": total_users,
            "active_users": active_users,
            "total_favorites": total_favorites,
            "average_rating": round(avg_rating, 2) if avg_rating else 0,
            "top_movies": list(top_movies),
            "top_users": [
                {"username": u.username, "favorites": u.fav_count} for u in top_users
            ],
        }

        # Cache results for 12 hours
        cache.set("analytics_report", report, 43200)

        logger.info("Analytics Report generated successfully")
        return {"status": "success", "report": report}

    except Exception as e:
        logger.error("Error generating analytics report: %s", e)
        raise self.retry(exc=e, countdown=600, max_retries=2)


@shared_task(
    bind=True,
    name="movies.tasks.bulk_cache_popular_movies",
    max_retries=2,
    default_retry_delay=300,
    priority=5,
)
def bulk_cache_popular_movies(self, movie_ids):
    """
    Bulk cache movie details for popular movies
    Used for preloading frequently accessed movies
    Queue: api
    Priority: 5 (medium)
    """
    try:
        logger.info("Starting bulk cache for %s movies", len(movie_ids))

        cached_count = 0
        for movie_id in movie_ids:
            try:
                details = tmdb_service.get_movie_details(movie_id)
                cache_key = f"movie_details_{movie_id}"
                cache.set(cache_key, details, 86400)
                cached_count += 1
            except Exception as e:
                logger.error(f"Error caching movie {movie_id}: {str(e)}")
                continue

        logger.info(
            "Bulk cache completed: %s/%s movies cached", cached_count, len(movie_ids)
        )
        return {"status": "success", "cached": cached_count, "total": len(movie_ids)}

    except Exception as e:
        logger.error("Error in bulk cache task: %s", e)
        raise self.retry(exc=e, countdown=300, max_retries=2)
