from django.conf import settings
from django.db import models


class FavoriteMovie(models.Model):
    """
    Stores a movie marked as favorite by a user.
    Includes key movie details for quick retrieval.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_movies",
    )
    movie_id = models.IntegerField()
    title = models.CharField(max_length=255)
    poster_path = models.CharField(max_length=255, blank=True, null=True)
    overview = models.TextField(blank=True, null=True)
    release_date = models.CharField(max_length=50, blank=True, null=True)
    vote_average = models.FloatField(default=0.0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Ensure each user can favorite a movie only once and order by newest first."""

        unique_together = ("user", "movie_id")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"
