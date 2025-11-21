from django.contrib import admin
from django.db.models import Avg, Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import FavoriteMovie


@admin.register(FavoriteMovie)
class FavoriteMovieAdmin(admin.ModelAdmin):
    """
    Custom admin view for FavoriteMovie model with enhanced features
    """

    list_display = [
        "movie_thumbnail",
        "title",
        "user_link",
        "vote_average_display",
        "release_date",
        "added_at_display",
        "view_on_tmdb",
    ]

    list_filter = [
        "added_at",
        "release_date",
    ]

    search_fields = ["title", "user__username", "user__email", "movie_id", "overview"]

    readonly_fields = ["added_at", "movie_poster_large", "movie_info_card"]

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))

        # If editing an existing FavoriteMovie, make movie_id readonly
        if obj and "movie_id" not in readonly_fields:
            readonly_fields.append("movie_id")

        return readonly_fields

    list_per_page = 25
    date_hierarchy = "added_at"

    def get_fieldsets(self, request, obj=None):
        """
        Optional: You can also customize fieldsets based on add/edit mode
        """
        if obj:  # Editing existing record
            return (
                (
                    "Movie Information",
                    {"fields": ("movie_id", "title", "movie_poster_large", "overview")},
                ),
                ("User & Date", {"fields": ("user", "added_at")}),
                (
                    "Movie Details",
                    {
                        "fields": ("poster_path", "release_date", "vote_average"),
                        "classes": ("collapse",),
                    },
                ),
                (
                    "Full Movie Data",
                    {"fields": ("movie_info_card",), "classes": ("collapse",)},
                ),
            )
        else:  # Adding new record
            return (
                (
                    "Required Information",
                    {"fields": ("user", "movie_id", "title")},
                ),
                (
                    "Movie Information",
                    {
                        "fields": (
                            "overview",
                            "poster_path",
                            "release_date",
                            "vote_average",
                        )
                    },
                ),
                (
                    "Full Movie Data",
                    {"fields": ("movie_info_card",), "classes": ("collapse",)},
                ),
            )

    actions = ["export_favorites", "clear_cache_for_selected"]

    def movie_thumbnail(self, obj):
        """Display small movie poster thumbnail"""
        if obj.poster_path:
            img_url = f"https://image.tmdb.org/t/p/w92{obj.poster_path}"
            return format_html(
                '<img src="{}" width="45" height="68" style="border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                img_url,
            )
        return format_html(
            '<div style="width: 45px; height: 68px; background: #e0e0e0; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #666;">No Image</div>'
        )

    movie_thumbnail.short_description = "Poster"

    def movie_poster_large(self, obj):
        """Display large movie poster in detail view"""
        if obj.poster_path:
            img_url = f"https://image.tmdb.org/t/p/w500{obj.poster_path}"
            return format_html(
                '<img src="{}" style="max-width: 300px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);" />',
                img_url,
            )
        return "No poster available"

    movie_poster_large.short_description = "Movie Poster"

    def user_link(self, obj):
        """Create clickable link to user's profile"""
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html(
            '<a href="{}" style="color: #417690; text-decoration: none;">{}</a>',
            url,
            obj.user.username,
        )

    user_link.short_description = "User"
    user_link.admin_order_field = "user__username"

    def vote_average_display(self, obj):
        """Display vote average with colored badge"""
        if obj.vote_average >= 8.0:
            color = "#4caf50"  # Green
            icon = "★"
        elif obj.vote_average >= 6.0:
            color = "#ff9800"  # Orange
            icon = "★"
        else:
            color = "#f44336"  # Red
            icon = "☆"

        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-weight: bold; font-size: 11px;">{} {}</span>',
            color,
            icon,
            obj.vote_average,
        )

    vote_average_display.short_description = "Rating"
    vote_average_display.admin_order_field = "vote_average"

    def added_at_display(self, obj):
        """Display formatted date"""
        return obj.added_at.strftime("%b %d, %Y %I:%M %p")

    added_at_display.short_description = "Added On"
    added_at_display.admin_order_field = "added_at"

    def view_on_tmdb(self, obj):
        """Link to TMDb movie page"""
        url = f"https://www.themoviedb.org/movie/{obj.movie_id}"
        return format_html(
            '<a href="{}" target="_blank" style="color: #01b4e4; text-decoration: none; font-weight: bold;">View on TMDb →</a>',
            url,
        )

    view_on_tmdb.short_description = "TMDb Link"

    def movie_info_card(self, obj):
        """Display comprehensive movie information card"""
        info = {
            "TMDb ID": obj.movie_id,
            "Title": obj.title,
            "Release Date": obj.release_date or "N/A",
            "Vote Average": obj.vote_average,
            "Overview": obj.overview or "No overview available",
            "Poster Path": obj.poster_path or "N/A",
            "Added By": obj.user.username,
            "Added On": obj.added_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

        html = """
            <div style="
                background: white;
                padding: 20px;
                border-radius: 12px;
                max-width: 600px;
                border-left: 4px solid #417690;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            ">
                <h4 style="margin-top: 0; margin-bottom: 15px; color: #417690; border-bottom: 1px solid #e9ecef; padding-bottom: 8px;">
                    Movie Information Card
                </h4>
            """

        for key, value in info.items():
            html += f"""
            <div style="
                margin-bottom: 12px; 
                padding: 8px 0;
                border-bottom: 1px solid #f8f9fa;
            ">
                <strong style="color: #495057; min-width: 120px; display: inline-block;">{key}:</strong>
                <span style="color: #212529;">{value}</span>
            </div>
            """

        html += "</div>"

        return mark_safe(html)

    movie_info_card.short_description = "Complete Movie Information"

    def export_favorites(self, request, queryset):
        """Export selected favorites as JSON"""
        data = []
        for favorite in queryset:
            data.append(
                {
                    "movie_id": favorite.movie_id,
                    "title": favorite.title,
                    "user": favorite.user.username,
                    "vote_average": favorite.vote_average,
                    "release_date": favorite.release_date,
                    "added_at": favorite.added_at.isoformat(),
                }
            )

        self.message_user(request, f"Exported {len(data)} favorites successfully.")

    export_favorites.short_description = "Export selected favorites as JSON"

    def clear_cache_for_selected(self, request, queryset):
        """Clear Redis cache for selected movie IDs"""
        from django.core.cache import cache

        movie_ids = queryset.values_list("movie_id", flat=True).distinct()

        cleared_count = 0
        for movie_id in movie_ids:
            cache_keys = [f"movie_details_{movie_id}", f"recommended_movies_{movie_id}"]
            for key in cache_keys:
                cache.delete(key)
                cleared_count += 1

        self.message_user(
            request,
            f"Cleared {cleared_count} cache entries for {len(movie_ids)} movies.",
        )

    clear_cache_for_selected.short_description = "Clear cache for selected movies"

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related("user")

    def changelist_view(self, request, extra_context=None):
        """Add statistics to the admin list view"""
        extra_context = extra_context or {}

        # Calculate statistics
        total_favorites = FavoriteMovie.objects.count()
        unique_users = FavoriteMovie.objects.values("user").distinct().count()
        unique_movies = FavoriteMovie.objects.values("movie_id").distinct().count()
        avg_rating = FavoriteMovie.objects.aggregate(Avg("vote_average"))[
            "vote_average__avg"
        ]

        # Top 5 most favorited movies
        top_movies = (
            FavoriteMovie.objects.values("movie_id", "title", "poster_path")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        extra_context["total_favorites"] = total_favorites
        extra_context["unique_users"] = unique_users
        extra_context["unique_movies"] = unique_movies
        extra_context["avg_rating"] = round(avg_rating, 2) if avg_rating else 0
        extra_context["top_movies"] = top_movies

        return super().changelist_view(request, extra_context)
