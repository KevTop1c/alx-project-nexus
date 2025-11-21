import logging

from django.contrib.auth import authenticate
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """
    Register a new user account
    """

    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        logger.info("API REQUEST: /api/users/register/ | data=%s", request.data)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        logger.info(
            "API RESPONSE: /api/users/register/ | status=201 | user=%s", user.username
        )

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


@swagger_auto_schema(
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["username", "password"],
        properties={
            "username": openapi.Schema(type=openapi.TYPE_STRING),
            "password": openapi.Schema(type=openapi.TYPE_STRING, format="password"),
        },
    ),
    responses={
        200: openapi.Response(
            "Login successful",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "access": openapi.Schema(type=openapi.TYPE_STRING),
                    "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                    "user": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "username": openapi.Schema(type=openapi.TYPE_STRING),
                            "email": openapi.Schema(type=openapi.TYPE_STRING),
                            "first_name": openapi.Schema(type=openapi.TYPE_STRING),
                            "last_name": openapi.Schema(type=openapi.TYPE_STRING),
                        },
                    ),
                },
            ),
        ),
        400: openapi.Response("Bad Request - Invalid input"),
        401: openapi.Response("Unauthorized - Invalid credentials"),
    },
)
class LoginView(TokenObtainPairView):
    """
    API endpoint for obtaining JWT tokens (login).
    """

    serializer_class = CustomTokenObtainPairSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    Get current user profile
    """
    logger.info("API REQUEST: /api/users/profile/ | user=%s", request.user.username)

    serializer = UserProfileSerializer(request.user.profile)

    logger.info(
        "API RESPONSE: /api/users/profile/ | status=200 | user=%s",
        request.user.username,
    )

    return Response(serializer.data)
