import logging
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.renderers import (
    JSONRenderer,
    BrowsableAPIRenderer,
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import FavoriteMovie
from .serializers import FavoriteMovieSerializer, AddFavoriteSerializer, MovieSerializer
from .utils.tmdb_service import TMDbService
from .tasks import send_favorite_notification, fetch_movie_details_async

logger = logging.getLogger(__name__)
tmdb_service = TMDbService()


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1,
        )
    ],
    responses={200: MovieSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def trending_movies(request):
    """
    Get trending movies (cached for 1 hour)
    """
    try:
        page = request.query_params.get("page", 1)
        logger.info(
            "API REQUEST: /api/movies/trending/ | page=%s | user=%s",
            page,
            request.user if request.user.is_authenticated else "anonymous",
        )

        data = tmdb_service.get_trending_movies(page=page)

        logger.info(
            "API RESPONSE: /api/movies/trending/ | status=200 | results=%s",
            len(data.get("results", [])),
        )
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("API ERROR: /api/movies/trending/ | error=%s", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecommendedMoviesPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 100


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "movie_id",
            openapi.IN_PATH,
            description="Movie ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1,
        ),
        openapi.Parameter(
            "limit",
            openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            default=20,
        ),
    ],
    responses={200: MovieSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def recommended_movies(request, movie_id):
    """
    Get recommended movies based on a movie ID (cached for 2 hours)
    """
    try:
        logger.info(
            "API REQUEST: /api/movies/recommendations/%s/ | user=%s",
            movie_id,
            request.user if request.user.is_authenticated else "anonymous",
        )

        data = tmdb_service.get_recommended_movies(movie_id)
        movies = data.get("results", [])

        # Use DRF pagination for automatic clickable links
        paginator = RecommendedMoviesPagination()
        paginated_movies = paginator.paginate_queryset(movies, request)

        if paginated_movies is not None:
            response = paginator.get_paginated_response(paginated_movies)

            logger.info(
                "API RESPONSE: /api/movies/recommendations/%s/ | status=200 | page=%s | showing=%s of %s",
                movie_id,
                request.GET.get("page", 1),
                len(paginated_movies),
                len(movies),
            )
            return response

        # Fallback if pagination not applied
        logger.info(
            "API RESPONSE: /api/movies/recommendations/%s/ | status=200 | results=%s",
            movie_id,
            len(movies),
        )
        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(
            "API ERROR: /api/movies/recommendations/%s/ | error=%s", movie_id, e
        )
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "query",
            openapi.IN_QUERY,
            description="Search query",
            type=openapi.TYPE_STRING,
            required=True,
        ),
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1,
        ),
    ],
    responses={200: MovieSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def search_movies(request):
    """
    Search for movies by title
    """
    try:
        query = request.query_params.get("query")
        if not query:
            return Response(
                {"error": "Query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        page = request.query_params.get("page", 1)
        data = tmdb_service.search_movies(query, page=page)
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "movie_id",
            openapi.IN_PATH,
            description="Movie ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        )
    ],
    responses={200: MovieSerializer()},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def movie_details(request, movie_id):
    """
    Get detailed information about a specific movie (cached for 24 hours)
    """
    try:
        logger.info(
            "API REQUEST: /api/movies/details/%s/ | user=%s",
            movie_id,
            request.user if request.user.is_authenticated else "anonymous",
        )

        data = tmdb_service.get_movie_details(movie_id)

        logger.info(
            "API RESPONSE: /api/movies/details/%s/ | status=200 | title=%s",
            movie_id,
            data.get("title", "N/A"),
        )
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("API ERROR: /api/movies/details/%s/ | error=%s", movie_id, e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FavoriteMovieListView(generics.ListAPIView):
    """
    Get list of user's favorite movies
    """

    serializer_class = FavoriteMovieSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoriteMovie.objects.filter(user=self.request.user)


class AddFavoriteView(generics.GenericAPIView):
    """
    Add a movie to your favorites.

    GET: Display form to add a favorite movie (Browsable API)
    POST: Add movie to your favorites
    """

    serializer_class = AddFavoriteSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    @swagger_auto_schema(
        operation_description="Display form for adding a favorite movie.",
        responses={200: AddFavoriteSerializer()},
    )
    def get(self, request, *args, **kwargs):
        """Display the input form in the browsable API."""
        serializer = self.get_serializer()
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Add a movie to your favorites.",
        request_body=AddFavoriteSerializer,
        responses={
            201: FavoriteMovieSerializer(),
            400: "Bad Request – Validation error or already in favorites",
        },
    )
    def post(self, request, *args, **kwargs):
        """Add a movie to your favorites."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Check if the movie already exists in favorites
        existing = FavoriteMovie.objects.filter(
            user=request.user, movie_id=validated_data["movie_id"]
        ).first()

        if existing:
            return Response(
                {"error": "Movie already in favorites"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a new favorite entry
        favorite = FavoriteMovie.objects.create(
            user=request.user,
            **validated_data,
        )

        # Send notification asynchronously
        send_favorite_notification.delay(
            user_id=request.user.id,
            movie_title=validated_data["title"],
        )

        # Fetch and cache full movie details asynchronously
        fetch_movie_details_async.delay(validated_data["movie_id"])

        logger.info(
            "User %s added movie %s to favorites",
            request.user.username,
            validated_data["title"],
        )

        return Response(
            FavoriteMovieSerializer(favorite).data,
            status=status.HTTP_201_CREATED,
        )


@swagger_auto_schema(
    method="delete",
    manual_parameters=[
        openapi.Parameter(
            "movie_id",
            openapi.IN_PATH,
            description="Movie ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        )
    ],
    responses={204: "Movie removed from favorites"},
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_favorite(request, movie_id):
    """
    Remove a movie from user's favorites
    """
    try:
        logger.info(
            "API REQUEST: /api/movies/favorites/remove/%s/ | user=%s",
            movie_id,
            request.user.username,
        )

        favorite = FavoriteMovie.objects.get(user=request.user, movie_id=movie_id)
        favorite.delete()

        logger.info(
            "API RESPONSE: /api/movies/favorites/remove/%s/ | status=204 | user=%s",
            movie_id,
            request.user.username,
        )
        return Response(
            {"message": "Movie removed from favorites"},
            status=status.HTTP_204_NO_CONTENT,
        )
    except FavoriteMovie.DoesNotExist:
        logger.warning(
            "API WARNING: /api/movies/favorites/remove/%s/ | status=404 | user=%s | error=Not in favorites",
            movie_id,
            request.user.username,
        )
        return Response(
            {"error": "Movie not found in favorites"}, status=status.HTTP_404_NOT_FOUND
        )


@swagger_auto_schema(
    method="get",
    responses={
        200: openapi.Response(
            "Cache statistics",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "total_commands": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "keyspace_hits": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "keyspace_misses": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "hit_rate": openapi.Schema(type=openapi.TYPE_NUMBER),
                },
            ),
        )
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cache_stats(request):
    """
    Get Redis cache statistics (admin only)
    """
    if not request.user.is_staff:
        logger.warning(
            "API UNAUTHORIZED: /api/movies/cache-stats/ | user=%s | error=Not staff",
            request.user.username,
        )
        return Response(
            {"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN
        )

    logger.info(
        "API REQUEST: /api/movies/cache-stats/ | user=%s", request.user.username
    )
    stats = tmdb_service.get_cache_stats()

    if stats:
        logger.info(
            "API RESPONSE: /api/movies/cache-stats/ | status=200 | hit_rate=%.2f%%",
            stats.get("hit_rate", 0),
        )
        return Response(stats, status=status.HTTP_200_OK)
    else:
        logger.error(
            "API ERROR: /api/movies/cache-stats/ | error=%s", "Failed to retrieve stats"
        )
        return Response(
            {"error": "Failed to retrieve cache stats"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
