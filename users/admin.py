from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import UserProfile

# Unregister the default User admin
admin.site.unregister(User)


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for UserProfile within User admin
    """

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"

    fields = ["bio", "created_at", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    Enhanced User admin with UserProfile inline and custom features
    """

    inlines = (UserProfileInline,)

    list_display = [
        "username",
        "email",
        "full_name_display",
        "is_active_display",
        "is_staff",
        "favorite_count",
        "date_joined_display",
        "last_login_display",
    ]

    list_filter = ["is_staff", "is_superuser", "is_active", "date_joined", "last_login"]

    search_fields = ["username", "first_name", "last_name", "email"]

    ordering = ["-date_joined"]

    list_per_page = 25

    actions = ["activate_users", "deactivate_users"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    def full_name_display(self, obj):
        """Display full name or indicate if not set"""
        full_name = obj.get_full_name()
        if full_name:
            return full_name
        return format_html('<span style="color: #999; font-style: italic;">Not set</span>')

    full_name_display.short_description = "Full Name"

    def is_active_display(self, obj):
        """Display active status with colored badge"""
        if obj.is_active:
            return format_html(
                '<span style="background: #4caf50; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="background: #f44336; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">✗ Inactive</span>'
        )

    is_active_display.short_description = "Status"
    is_active_display.admin_order_field = "is_active"

    def favorite_count(self, obj):
        """Display count of user's favorite movies"""
        count = obj.favorite_movies.count()
        if count > 0:
            url = f"{reverse('admin:movies_favoritemovie_changelist')}?user__id__exact={obj.id}"
            return format_html(
                '<a href="{}" style="color: #417690; text-decoration: none; font-weight: bold;">{} movies</a>',
                url,
                count,
            )
        return format_html('<span style="color: #999;">0 movies</span>')

    favorite_count.short_description = "Favorites"

    def date_joined_display(self, obj):
        """Display formatted join date"""
        return obj.date_joined.strftime("%b %d, %Y")

    date_joined_display.short_description = "Joined"
    date_joined_display.admin_order_field = "date_joined"

    def last_login_display(self, obj):
        """Display formatted last login"""
        if obj.last_login:
            return obj.last_login.strftime("%b %d, %Y %I:%M %p")
        return format_html('<span style="color: #999;">Never</span>')

    last_login_display.short_description = "Last Login"
    last_login_display.admin_order_field = "last_login"

    def activate_users(self, request, queryset):
        """Bulk activate users"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) activated successfully.")

    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        """Bulk deactivate users"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) deactivated successfully.")

    deactivate_users.short_description = "Deactivate selected users"

    def get_queryset(self, request):
        """Optimize queries with prefetch_related"""
        qs = super().get_queryset(request)
        return qs.prefetch_related("favorite_movies")

    def changelist_view(self, request, extra_context=None):
        """Add user statistics to the admin list view"""
        extra_context = extra_context or {}

        # Calculate statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        staff_users = User.objects.filter(is_staff=True).count()
        users_with_favorites = User.objects.annotate(fav_count=Count("favorite_movies")).filter(fav_count__gt=0).count()

        extra_context["total_users"] = total_users
        extra_context["active_users"] = active_users
        extra_context["staff_users"] = staff_users
        extra_context["users_with_favorites"] = users_with_favorites

        return super().changelist_view(request, extra_context)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Standalone admin for UserProfile model
    """

    list_display = [
        "user_link",
        "user_email",
        "bio_preview",
        "created_at_display",
        "updated_at_display",
    ]

    search_fields = ["user__username", "user__email", "bio"]

    list_filter = ["created_at", "updated_at"]

    readonly_fields = ["user", "created_at", "updated_at"]

    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        ("User Information", {"fields": ("user",)}),
        ("Profile Details", {"fields": ("bio",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def user_link(self, obj):
        """Create clickable link to user"""
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html(
            '<a href="{}" style="color: #417690; text-decoration: none; font-weight: bold;">{}</a>',
            url,
            obj.user.username,
        )

    user_link.short_description = "Username"
    user_link.admin_order_field = "user__username"

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email or format_html('<span style="color: #999;">No email</span>')

    user_email.short_description = "Email"
    user_email.admin_order_field = "user__email"

    def bio_preview(self, obj):
        """Display bio preview (first 100 characters)"""
        if obj.bio:
            preview = obj.bio[:100]
            if len(obj.bio) > 100:
                preview += "..."
            return preview
        return format_html('<span style="color: #999; font-style: italic;">No bio</span>')

    bio_preview.short_description = "Bio"

    def created_at_display(self, obj):
        """Display formatted creation date"""
        return obj.created_at.strftime("%b %d, %Y")

    created_at_display.short_description = "Created"
    created_at_display.admin_order_field = "created_at"

    def updated_at_display(self, obj):
        """Display formatted update date"""
        return obj.updated_at.strftime("%b %d, %Y %I:%M %p")

    updated_at_display.short_description = "Last Updated"
    updated_at_display.admin_order_field = "updated_at"

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related("user")


# Customize admin site header and title
admin.site.site_header = "Movie Recommendation Admin"
admin.site.site_title = "Movie Admin Portal"
admin.site.index_title = "Welcome to Movie Recommendation Administration"
