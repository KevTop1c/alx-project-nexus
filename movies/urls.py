from django.urls import path
from .views import (
    trending_movies,
    recommended_movies,
    search_movies,
    movie_details,
    FavoriteMovieListView,
    add_favorite,
    remove_favorite,
    cache_stats,
)

urlpatterns = [
    path("trending/", trending_movies, name="trending-movies"),
    path(
        "recommendations/<int:movie_id>/", recommended_movies, name="recommended-movies"
    ),
    path("search/", search_movies, name="search-movies"),
    path("details/<int:movie_id>/", movie_details, name="movie-details"),
    path("favorites/", FavoriteMovieListView.as_view(), name="favorite-movies"),
    path("favorites/add/", add_favorite, name="add-favorite"),
    path("favorites/remove/<int:movie_id>/", remove_favorite, name="remove-favorite"),
    path("cache-stats/", cache_stats, name="cache-stats"),
]
