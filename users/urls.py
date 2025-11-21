from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, RegisterView, profile_view

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("profile/", profile_view, name="profile"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
