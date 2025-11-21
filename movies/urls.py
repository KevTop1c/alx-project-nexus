from django.urls import path

from .views import (
    AddFavoriteView,
    FavoriteMovieListView,
    cache_stats,
    movie_details,
    recommended_movies,
    remove_favorite,
    search_movies,
    trending_movies,
)

urlpatterns = [
    path("trending/", trending_movies, name="trending-movies"),
    path("recommendations/<int:movie_id>/", recommended_movies, name="recommended-movies"),
    path("search/", search_movies, name="search-movies"),
    path("details/<int:movie_id>/", movie_details, name="movie-details"),
    path("favorites/", FavoriteMovieListView.as_view(), name="favorite-movies"),
    path("favorites/add/", AddFavoriteView.as_view(), name="add-favorite"),
    path("favorites/remove/<int:movie_id>/", remove_favorite, name="remove-favorite"),
    path("cache-stats/", cache_stats, name="cache-stats"),
]
