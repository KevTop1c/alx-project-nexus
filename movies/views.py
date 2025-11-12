from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import FavoriteMovie
from .serializers import FavoriteMovieSerializer, AddFavoriteSerializer, MovieSerializer
from .tmdb_service import TMDbService

tmdb_service = TMDbService()


@api_view(["GET"])
@permission_classes([AllowAny])
def trending_movies(request):
    """
    Get trending movies (cached for 1 hour)
    """
    try:
        page = request.query_params.get("page", 1)
        data = tmdb_service.get_trending_movies(page=page)
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def recommended_movies(request, movie_id):
    """
    Get recommended movies based on a movie ID (cached for 2 hours)
    """
    try:
        data = tmdb_service.get_recommended_movies(movie_id)
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


@api_view(["GET"])
@permission_classes([AllowAny])
def movie_details(request, movie_id):
    """
    Get detailed information about a specific movie (cached for 24 hours)
    """
    try:
        data = tmdb_service.get_movie_details(movie_id)
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FavoriteMovieListView(generics.ListAPIView):
    """
    Get list of the user's favorite movies
    """

    serializer_class = FavoriteMovieSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoriteMovie.objects.filter(user=self.request.user)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_favorite(request):
    """
    Add a movie to user's favorites
    """
    serializer = AddFavoriteSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data

    # Check if already exists
    existing = FavoriteMovie.objects.filter(
        user=request.user, movie_id=validated_data["movie_id"]
    ).first()

    if existing:
        return Response(
            {"error": "Movie already in favorites"}, status=status.HTTP_400_BAD_REQUEST
        )

    favorite = FavoriteMovie.objects.create(user=request.user, **validated_data)

    return Response(
        FavoriteMovieSerializer(favorite).data, status=status.HTTP_201_CREATED
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_favorite(request, movie_id):
    """
    Remove a movie from user's favorites
    """
    try:
        favorite = FavoriteMovie.objects.get(user=request.user, movie_id=movie_id)
        favorite.delete()
        return Response(
            {"message": "Movie removed from favorites"},
            status=status.HTTP_204_NO_CONTENT,
        )
    except FavoriteMovie.DoesNotExist:
        return Response(
            {"error": "Movie not found in favorites"}, status=status.HTTP_404_NOT_FOUND
        )
