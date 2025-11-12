from rest_framework import serializers
from .models import FavoriteMovie


class MovieSerializer(serializers.Serializer):
    """Serializes movie data from external API responses."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    overview = serializers.CharField()
    poster_path = serializers.CharField(allow_null=True)
    backdrop_path = serializers.CharField(allow_null=True)
    release_date = serializers.CharField()
    vote_average = serializers.FloatField()
    vote_count = serializers.IntegerField()
    popularity = serializers.FloatField()


class FavoriteMovieSerializer(serializers.ModelSerializer):
    """Serializes FavoriteMovie model for read operations."""

    class Meta:
        model = FavoriteMovie
        fields = [
            "id",
            "movie_id",
            "title",
            "poster_path",
            "overview",
            "release_date",
            "vote_average",
            "added_at",
        ]
        read_only_fields = ["id", "added_at"]


class AddFavoriteSerializer(serializers.Serializer):
    """Validates and serializes data for adding new favorite movies."""

    movie_id = serializers.IntegerField(required=True)
    title = serializers.CharField(required=True, max_length=255)
    poster_path = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    overview = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    release_date = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    vote_average = serializers.FloatField(required=False, default=0.0)
